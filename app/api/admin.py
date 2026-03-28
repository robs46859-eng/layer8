from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, require_admin_auth
from app.schemas.admin import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyResponse,
    TenantCreateRequest,
    TenantResponse,
    TenantUpdateRequest,
)
from app.services.api_keys import APIKeyAdminService
from app.services.tenants import TenantService

admin_router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_auth)])


def _to_tenant_response(tenant) -> TenantResponse:
    return TenantResponse.model_validate(tenant, from_attributes=True)


def _to_api_key_response(api_key) -> APIKeyResponse:
    return APIKeyResponse.model_validate(api_key, from_attributes=True)


def _to_api_key_create_response(api_key, raw_key: str) -> APIKeyCreateResponse:
    payload = _to_api_key_response(api_key).model_dump()
    payload["api_key"] = raw_key
    return APIKeyCreateResponse(**payload)


@admin_router.get("/tenants", response_model=list[TenantResponse])
def list_tenants(session: Session = Depends(get_db_session)) -> list[TenantResponse]:
    service = TenantService(session)
    return [_to_tenant_response(tenant) for tenant in service.list_tenants()]


@admin_router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: TenantCreateRequest, session: Session = Depends(get_db_session)
) -> TenantResponse:
    service = TenantService(session)
    try:
        tenant = service.create_tenant(payload.tenant_id, payload.name, payload.data_residency)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_tenant_response(tenant)


@admin_router.get("/tenants/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: str, session: Session = Depends(get_db_session)) -> TenantResponse:
    service = TenantService(session)
    try:
        tenant = service.get_tenant(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_tenant_response(tenant)


@admin_router.patch("/tenants/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: str, payload: TenantUpdateRequest, session: Session = Depends(get_db_session)
) -> TenantResponse:
    service = TenantService(session)
    try:
        tenant = service.update_tenant(
            tenant_id,
            name=payload.name,
            data_residency=payload.data_residency,
            status=payload.status,
        )
    except ValueError as exc:
        code = status.HTTP_404_NOT_FOUND if "not found" in str(exc) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    return _to_tenant_response(tenant)


@admin_router.post("/tenants/{tenant_id}/disable", response_model=TenantResponse)
def disable_tenant(tenant_id: str, session: Session = Depends(get_db_session)) -> TenantResponse:
    service = TenantService(session)
    try:
        tenant = service.disable_tenant(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_tenant_response(tenant)


@admin_router.get("/tenants/{tenant_id}/api-keys", response_model=list[APIKeyResponse])
def list_api_keys(
    tenant_id: str, session: Session = Depends(get_db_session)
) -> list[APIKeyResponse]:
    service = APIKeyAdminService(session)
    try:
        keys = service.list_api_keys(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [_to_api_key_response(api_key) for api_key in keys]


@admin_router.post(
    "/tenants/{tenant_id}/api-keys",
    response_model=APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_api_key(
    tenant_id: str,
    payload: APIKeyCreateRequest,
    session: Session = Depends(get_db_session),
) -> APIKeyCreateResponse:
    service = APIKeyAdminService(session)
    try:
        api_key, raw_key = service.create_api_key(tenant_id, payload.scopes, payload.allowed_models)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_api_key_create_response(api_key, raw_key)


@admin_router.post("/api-keys/{key_id}/revoke", response_model=APIKeyResponse)
def revoke_api_key(key_id: str, session: Session = Depends(get_db_session)) -> APIKeyResponse:
    service = APIKeyAdminService(session)
    try:
        api_key = service.revoke_api_key(key_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_api_key_response(api_key)


@admin_router.post("/api-keys/{key_id}/rotate", response_model=APIKeyCreateResponse)
def rotate_api_key(key_id: str, session: Session = Depends(get_db_session)) -> APIKeyCreateResponse:
    service = APIKeyAdminService(session)
    try:
        api_key, raw_key = service.rotate_api_key(key_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_api_key_create_response(api_key, raw_key)
