from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, require_admin_auth
from app.schemas.pilot import (
    PilotApplicationAccepted,
    PilotApplicationAdminResponse,
    PilotApplicationCreate,
    PilotStatus,
)
from app.services.pilot_applications import PilotApplicationService

pilot_router = APIRouter(prefix="/v1", tags=["pilot"])
admin_pilot_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_auth)],
)
DbSession = Annotated[Session, Depends(get_db_session)]


@pilot_router.post(
    "/pilot-applications",
    response_model=PilotApplicationAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_pilot_application(
    payload: PilotApplicationCreate,
    session: DbSession,
) -> PilotApplicationAccepted:
    PilotApplicationService(session).create_application(payload)
    return PilotApplicationAccepted()


@admin_pilot_router.get(
    "/pilot-applications",
    response_model=list[PilotApplicationAdminResponse],
)
def list_pilot_applications(
    session: DbSession,
    application_status: Annotated[
        PilotStatus | None,
        Query(alias="status"),
    ] = None,
    source: Annotated[
        str | None,
        Query(min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9._-]*$"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[PilotApplicationAdminResponse]:
    applications = PilotApplicationService(session).list_applications(
        application_status=application_status,
        source=source,
        limit=limit,
        offset=offset,
    )
    return [
        PilotApplicationAdminResponse.model_validate(
            application,
            from_attributes=True,
        )
        for application in applications
    ]
