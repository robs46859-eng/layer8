from datetime import datetime

from pydantic import BaseModel, Field


class TenantCreateRequest(BaseModel):
    tenant_id: str = Field(min_length=3, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    data_residency: str | None = Field(default=None, max_length=64)
    clerk_organization_id: str | None = Field(default=None, min_length=3, max_length=64)


class TenantUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    data_residency: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, pattern="^(active|disabled)$")
    clerk_organization_id: str | None = Field(default=None, min_length=3, max_length=64)


class TenantResponse(BaseModel):
    id: str
    name: str
    status: str
    data_residency: str | None
    clerk_organization_id: str | None
    created_at: datetime
    updated_at: datetime
    disabled_at: datetime | None


class APIKeyCreateRequest(BaseModel):
    scopes: list[str] = Field(default_factory=lambda: ["inference:invoke"])
    allowed_models: list[str] = Field(default_factory=list)


class APIKeyResponse(BaseModel):
    id: str
    tenant_id: str
    prefix: str
    scopes: list[str]
    allowed_models: list[str]
    status: str
    created_at: datetime
    updated_at: datetime
    revoked_at: datetime | None


class APIKeyCreateResponse(APIKeyResponse):
    api_key: str
