"""
Routes serving PawsMemories' BO-4 Thermal Cascade: observe / plan / verify.

Auth reuses Layer8's existing tenant API-key system (AuthService/APIKeyStore)
via the X-API-Key header -- the same mechanism /v1/proxy/infer uses. These
routes intentionally bypass InferencePipeline (rate limiting, response
caching, plugin runtime, audit logging) because that pipeline is built
around single-turn chat completions, not multi-image structured JSON with a
schema-repair retry loop. If this integration graduates past MVP, revisit
folding these into the pipeline's before/after plugin hooks rather than
duplicating rate-limit/audit logic here.

Spatial execution requires an active subscription, the spatial_intelligence
plan entitlement, and a spatial:invoke API-key scope.
"""

import logging
from typing import NoReturn

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.config import get_settings
from app.core.security import split_api_key, verify_api_secret
from app.schemas.spatial import (
    SpatialHealthResponse,
    SpatialObserveOutput,
    SpatialObserveRequest,
    SpatialPlanOutput,
    SpatialPlanRequest,
    SpatialVerifyOutput,
    SpatialVerifyRequest,
)
from app.services.auth import APIKeyRecord, InMemoryAPIKeyStore, PostgresAPIKeyStore
from app.services.entitlements import (
    BillingAccessError,
    EntitlementAccessError,
    enforce_entitlement,
)
from app.services.spatial_reasoning import SpatialReasoningError, run_observe, run_plan, run_verify

logger = logging.getLogger(__name__)

spatial_router = APIRouter(prefix="/v1/spatial", tags=["spatial"])

_settings = get_settings()
_key_store = (
    PostgresAPIKeyStore()
    if _settings.backend_mode == "self_hosted"
    else InMemoryAPIKeyStore.from_settings(_settings)
)

_ERROR_STATUS = {
    "NOT_CONFIGURED": status.HTTP_503_SERVICE_UNAVAILABLE,
    "NO_REFERENCE_IMAGES": status.HTTP_400_BAD_REQUEST,
    "NO_DRAFT_IMAGES": status.HTTP_400_BAD_REQUEST,
    "UPSTREAM_ERROR": status.HTTP_502_BAD_GATEWAY,
    "INVALID_MODEL_OUTPUT": status.HTTP_502_BAD_GATEWAY,
}


async def require_spatial_auth(x_api_key: str = Header(..., alias="X-API-Key")) -> APIKeyRecord:
    try:
        prefix, secret = split_api_key(x_api_key)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    record = await _key_store.get_by_prefix(prefix)
    if record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unknown or inactive api key")
    if record.tenant_status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="tenant is inactive")
    if record.key_status != "active" or not record.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="api key is inactive")
    if not verify_api_secret(record.prefix, secret, record.secret_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")
    try:
        enforce_entitlement(
            subscription_status=record.billing_status,
            payment_grace_ends_at=record.payment_grace_ends_at,
            entitlements=set(record.billing_entitlements or set()),
            required_entitlement="spatial_intelligence",
        )
    except BillingAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(exc),
        ) from exc
    except EntitlementAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    if "spatial:invoke" not in record.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="missing scope spatial:invoke",
        )
    return record


def _raise_for(exc: SpatialReasoningError) -> NoReturn:
    code = _ERROR_STATUS.get(exc.code, status.HTTP_502_BAD_GATEWAY)
    raise HTTPException(status_code=code, detail={"code": exc.code, "message": str(exc)}) from exc


@spatial_router.post("/observe", response_model=SpatialObserveOutput)
async def observe(
    payload: SpatialObserveRequest,
    auth: APIKeyRecord = Depends(require_spatial_auth),  # noqa: B008 -- FastAPI DI idiom, ruff false-positive here (see app/api/admin.py for same pre-existing pattern)
) -> SpatialObserveOutput:
    settings = get_settings()
    logger.info({"event": "spatial_observe_request", "tenant_id": auth.tenant_id, "image_count": len(payload.referenceImages)})
    try:
        return await run_observe(settings, payload.referenceImages, payload.scaleAnchor)
    except SpatialReasoningError as exc:
        _raise_for(exc)


@spatial_router.post("/plan", response_model=SpatialPlanOutput)
async def plan(
    payload: SpatialPlanRequest,
    auth: APIKeyRecord = Depends(require_spatial_auth),  # noqa: B008 -- FastAPI DI idiom, ruff false-positive here (see app/api/admin.py for same pre-existing pattern)
) -> SpatialPlanOutput:
    settings = get_settings()
    logger.info({"event": "spatial_plan_request", "tenant_id": auth.tenant_id})
    try:
        return await run_plan(
            settings,
            payload.observation,
            payload.userPrompt,
            payload.targetEnvelopeMm.model_dump(),
            payload.scaleAnchor,
            payload.attachmentInterface.model_dump() if payload.attachmentInterface else None,
        )
    except SpatialReasoningError as exc:
        _raise_for(exc)


@spatial_router.post("/verify", response_model=SpatialVerifyOutput)
async def verify(
    payload: SpatialVerifyRequest,
    auth: APIKeyRecord = Depends(require_spatial_auth),  # noqa: B008 -- FastAPI DI idiom, ruff false-positive here (see app/api/admin.py for same pre-existing pattern)
) -> SpatialVerifyOutput:
    settings = get_settings()
    logger.info({"event": "spatial_verify_request", "tenant_id": auth.tenant_id, "image_count": len(payload.draftImages)})
    try:
        return await run_verify(settings, payload.observation, payload.draftImages, payload.attemptHash)
    except SpatialReasoningError as exc:
        _raise_for(exc)


@spatial_router.get("/health", response_model=SpatialHealthResponse)
async def spatial_health() -> SpatialHealthResponse:
    settings = get_settings()
    # Liveness only: confirms Gemini credentials are present, does not spend
    # a real API call on every health check. observe/plan/verify/math all
    # share the same upstream provider, so they rise and fall together today.
    healthy = "healthy" if settings.gemini_api_key else "unhealthy"
    return SpatialHealthResponse(
        spatial_observe=healthy,
        spatial_plan=healthy,
        spatial_math=healthy,
        spatial_verify=healthy,
    )
