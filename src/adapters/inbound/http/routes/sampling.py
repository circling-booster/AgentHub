"""Sampling HITL API Routes (Phase 6, Step 6.3)"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from src.adapters.inbound.http.schemas.sampling import (
    SamplingApproveResponse,
    SamplingRejectRequest,
    SamplingRejectResponse,
    SamplingRequestListResponse,
    SamplingRequestSchema,
)
from src.config.container import Container
from src.domain.ports.outbound.orchestrator_port import OrchestratorPort
from src.domain.services.sampling_service import SamplingService

router = APIRouter(prefix="/api/sampling", tags=["sampling"])


@router.get("/requests", response_model=SamplingRequestListResponse)
@inject
def list_sampling_requests(
    sampling_service: SamplingService = Depends(Provide[Container.sampling_service]),
):
    """대기 중인 Sampling 요청 목록"""
    requests = sampling_service.list_pending()
    return SamplingRequestListResponse(
        requests=[SamplingRequestSchema.from_entity(r) for r in requests]
    )


@router.post("/requests/{request_id}/approve", response_model=SamplingApproveResponse)
@inject
async def approve_sampling_request(
    request_id: str,
    sampling_service: SamplingService = Depends(Provide[Container.sampling_service]),
    orchestrator: OrchestratorPort = Depends(Provide[Container.orchestrator_adapter]),
):
    """Sampling 요청 승인 + LLM 실행 (Method C)

    1. LLM 호출 (orchestrator.generate_response)
    2. 결과를 sampling_service.approve()로 시그널
    3. RegistryService의 콜백이 깨어나서 MCP 서버에 전달
    """
    # 1. 요청 조회
    request = sampling_service.get_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    # 2. LLM 호출 (Port 사용 - 헥사고날 위반 아님)
    llm_result = await orchestrator.generate_response(
        messages=request.messages,
        model=request.model_preferences.get("model") if request.model_preferences else None,
        system_prompt=request.system_prompt,
        max_tokens=request.max_tokens,
    )

    # 3. 시그널 (콜백이 깨어남)
    await sampling_service.approve(request_id, llm_result)

    return SamplingApproveResponse(status="approved", result=llm_result)


@router.post("/requests/{request_id}/reject", response_model=SamplingRejectResponse)
@inject
async def reject_sampling_request(
    request_id: str,
    reject_body: SamplingRejectRequest,
    sampling_service: SamplingService = Depends(Provide[Container.sampling_service]),
):
    """Sampling 요청 거부"""
    success = await sampling_service.reject(request_id, reject_body.reason)
    if not success:
        raise HTTPException(status_code=404, detail="Request not found")
    return SamplingRejectResponse(status="rejected")
