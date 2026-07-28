from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import PilotApplication
from app.schemas.pilot import PilotApplicationCreate


class PilotApplicationService:
    def __init__(self, session: Session):
        self.session = session

    def create_application(
        self, payload: PilotApplicationCreate
    ) -> PilotApplication | None:
        # Return the same public response for honeypot submissions, but do not
        # persist them or log their potentially hostile contents.
        if payload.website:
            return None

        application = PilotApplication(
            id=f"pilot_{uuid4().hex}",
            contact_name=payload.contact_name,
            work_email=str(payload.work_email),
            company=payload.company,
            role=payload.role,
            use_case=payload.use_case,
            timeline=payload.timeline,
            source=payload.source,
            status="new",
            consent_to_contact=True,
        )
        self.session.add(application)
        self.session.commit()
        self.session.refresh(application)
        return application

    def list_applications(
        self,
        *,
        application_status: str | None = None,
        source: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PilotApplication]:
        statement: Select[tuple[PilotApplication]] = select(PilotApplication)
        if application_status is not None:
            statement = statement.where(
                PilotApplication.status == application_status
            )
        if source is not None:
            statement = statement.where(PilotApplication.source == source)
        statement = statement.order_by(
            PilotApplication.created_at.desc(),
            PilotApplication.id.desc(),
        ).limit(limit).offset(offset)
        return list(self.session.scalars(statement))
