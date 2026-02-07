"""Elicitation HITL API Routes (Phase 6, Step 6.4)"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from src.adapters.inbound.http.schemas.elicitation import (
    ElicitationRequestListResponse,
    ElicitationRequestSchema,
    ElicitationRespondRequest,
    ElicitationRespondResponse,
)
from src.config.container import Container
from src.domain.services.elicitation_service import ElicitationService

router = APIRouter(prefix="/api/elicitation", tags=["elicitation"])


@router.get("/requests", response_model=ElicitationRequestListResponse)
@inject
async def list_elicitation_requests(
    elicitation_service: ElicitationService = Depends(Provide[Container.elicitation_service]),
):
    """대기 중인 Elicitation 요청 목록"""
    requests = elicitation_service.list_pending()
    return ElicitationRequestListResponse(
        requests=[ElicitationRequestSchema.from_entity(r) for r in requests]
    )


@router.post("/requests/{request_id}/respond", response_model=ElicitationRespondResponse)
@inject
async def respond_elicitation_request(
    request_id: str,
    respond_body: ElicitationRespondRequest,
    elicitation_service: ElicitationService = Depends(Provide[Container.elicitation_service]),
):
    """Elicitation 응답 (accept/decline/cancel)"""
    from src.domain.entities.elicitation_request import ElicitationAction

    action_enum = ElicitationAction(respond_body.action)

    success = await elicitation_service.respond(request_id, action_enum, respond_body.content)
    if not success:
        raise HTTPException(status_code=404, detail="Request not found")

    return ElicitationRespondResponse(status=respond_body.action)
