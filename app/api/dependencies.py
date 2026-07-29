import hashlib
import hmac
from collections.abc import Iterator
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Tenant
from app.db.session import get_session_factory
from app.services.tenants import TenantService


def get_db_session() -> Iterator:
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def require_admin_auth(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.admin_api_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin auth is not configured",
        )
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing admin authorization",
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid admin authorization format",
        )
    if not hmac.compare_digest(token, settings.admin_api_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="invalid admin token",
        )


def require_customer_tenant(
    session: Annotated[Session, Depends(get_db_session)],
    authorization: str | None = Header(default=None),
) -> Tenant:
    settings = get_settings()
    if not settings.clerk_jwt_key or not settings.clerk_issuer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="customer authentication is not configured",
        )
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing customer authorization",
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid customer authorization format",
        )

    try:
        claims = jwt.decode(
            token,
            settings.clerk_jwt_key.replace("\\n", "\n"),
            algorithms=["RS256"],
            issuer=settings.clerk_issuer,
            options={
                "verify_aud": False,
                "require": ["exp", "iat", "nbf", "iss", "sub"],
            },
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid customer session",
        ) from exc

    authorized_parties = {
        party.strip()
        for party in settings.clerk_authorized_parties.split(",")
        if party.strip()
    }
    if authorized_parties and claims.get("azp") not in authorized_parties:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="customer session has an invalid authorized party",
        )
    organization_id = claims.get("org_id")
    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="select a customer organization before accessing billing",
        )

    tenant = session.scalar(
        select(Tenant).where(Tenant.clerk_organization_id == organization_id)
    )
    if tenant is None and settings.self_service_signup_enabled:
        organization_digest = hashlib.sha256(organization_id.encode()).hexdigest()
        try:
            tenant = TenantService(session).create_tenant(
                tenant_id=f"tenant_self_{organization_digest[:24]}",
                name=f"Self-service workspace {organization_digest[:12]}",
                data_residency=None,
                clerk_organization_id=organization_id,
            )
        except IntegrityError:
            session.rollback()
            tenant = session.scalar(
                select(Tenant).where(
                    Tenant.clerk_organization_id == organization_id
                )
            )
    if tenant is None or tenant.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="organization is not linked to an active Layer8 tenant",
        )
    return tenant
