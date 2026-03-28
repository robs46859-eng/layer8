from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import Tenant


class TenantService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_tenants(self) -> list[Tenant]:
        return self.session.query(Tenant).order_by(Tenant.created_at.asc()).all()

    def get_tenant(self, tenant_id: str) -> Tenant:
        tenant = self.session.get(Tenant, tenant_id)
        if tenant is None:
            raise ValueError("tenant not found")
        return tenant

    def create_tenant(self, tenant_id: str, name: str, data_residency: str | None) -> Tenant:
        if self.session.get(Tenant, tenant_id) is not None:
            raise ValueError("tenant id already exists")
        name_exists = self.session.query(Tenant).filter(Tenant.name == name).one_or_none()
        if name_exists is not None:
            raise ValueError("tenant name already exists")
        now = datetime.now(UTC).replace(tzinfo=None)
        tenant = Tenant(
            id=tenant_id,
            name=name,
            status="active",
            data_residency=data_residency,
            created_at=now,
            updated_at=now,
            disabled_at=None,
        )
        self.session.add(tenant)
        self.session.commit()
        self.session.refresh(tenant)
        return tenant

    def update_tenant(
        self,
        tenant_id: str,
        *,
        name: str | None,
        data_residency: str | None,
        status: str | None,
    ) -> Tenant:
        tenant = self.get_tenant(tenant_id)
        if name is not None and name != tenant.name:
            name_exists = self.session.query(Tenant).filter(Tenant.name == name).one_or_none()
            if name_exists is not None:
                raise ValueError("tenant name already exists")
            tenant.name = name
        if data_residency is not None:
            tenant.data_residency = data_residency
        if status is not None:
            tenant.status = status
            tenant.disabled_at = (
                datetime.now(UTC).replace(tzinfo=None) if status == "disabled" else None
            )
        tenant.updated_at = datetime.now(UTC).replace(tzinfo=None)
        self.session.add(tenant)
        self.session.commit()
        self.session.refresh(tenant)
        return tenant

    def disable_tenant(self, tenant_id: str) -> Tenant:
        return self.update_tenant(tenant_id, name=None, data_residency=None, status="disabled")
