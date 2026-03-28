from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.pipeline import build_pipeline
from app.schemas.inference import ErrorResponse, InferenceRequest, InferenceResponse

router = APIRouter()
pipeline = build_pipeline()


@router.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/v1/proxy/infer",
    response_model=InferenceResponse,
    responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
async def infer(
    payload: InferenceRequest,
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key"),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
) -> InferenceResponse:
    try:
        return await pipeline.execute(
            payload=payload,
            presented_api_key=x_api_key,
            idempotency_key=x_idempotency_key,
            client_host=request.client.host if request.client else None,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        code = status.HTTP_429_TOO_MANY_REQUESTS if "rate limit" in str(exc).lower() else 400
        raise HTTPException(status_code=code, detail=str(exc)) from exc
