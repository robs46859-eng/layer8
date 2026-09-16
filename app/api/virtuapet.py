"""Signed VirtuaPet proofs and policy decisions, disabled by default."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.schemas.virtuapet import LinkProofRequest, LinkProofResponse, PolicyRequest, PolicyResponse
from app.services.virtuapet import VirtuaPetService, get_virtuapet_service, integration_error


class PrivateContractRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handler(request: Request):
            # Prevent default FastAPI validation errors from echoing bearer proof inputs.
            try:
                size = 0
                chunks = []
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 32768:
                        raise integration_error("virtuapet_request_too_large", 413)
                    chunks.append(chunk)
                request._body = b"".join(chunks)
                response = await original(request)
                response.headers["Cache-Control"] = "no-store"
                return response
            except RequestValidationError as exc:
                raise integration_error("virtuapet_invalid_request", 422) from exc
            except HTTPException as exc:
                exc.headers = {**(exc.headers or {}), "Cache-Control": "no-store"}
                raise
            except Exception as exc:
                # SQL/network/parser details must not reveal request or credential data.
                raise integration_error("virtuapet_unavailable") from exc

        return handler


virtuapet_router = APIRouter(
    prefix="/v1/integrations/virtuapet", tags=["virtuapet"], route_class=PrivateContractRoute,
)
Service = Annotated[VirtuaPetService, Depends(get_virtuapet_service)]
Database = Annotated[Session, Depends(get_db_session)]


@virtuapet_router.post("/link-proof", response_model=LinkProofResponse)
async def link_proof(
    payload: LinkProofRequest, response: Response, service: Service, session: Database,
    authorization: str | None = Header(default=None),
) -> LinkProofResponse:
    identity = service.authenticate_clerk(session, authorization)
    token = await service.link_proof(payload, identity)
    response.headers["Cache-Control"] = "no-store"
    return LinkProofResponse(proofToken=token)


@virtuapet_router.post("/policy", response_model=PolicyResponse)
async def policy(
    payload: PolicyRequest, response: Response, service: Service, session: Database,
    authorization: str | None = Header(default=None),
) -> PolicyResponse:
    record = await service.authenticate_key(authorization)
    proof = service.validate_proof(payload, record, session)
    await service.limiter.reserve_request(record.tenant_id, str(payload.requestId))
    token = service.decision(payload, record, proof)
    response.headers["Cache-Control"] = "no-store"
    return PolicyResponse(decisionToken=token)
