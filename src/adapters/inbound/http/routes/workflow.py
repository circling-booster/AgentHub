"""Workflow Management API Routes

Workflow 생성, 조회, 실행, 삭제 엔드포인트
"""

import json
import logging
from uuid import uuid4

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from src.adapters.inbound.http.schemas.workflow import (
    CreateWorkflowRequest,
    ExecuteWorkflowRequest,
    WorkflowResponse,
    WorkflowStepSchema,
)
from src.config.container import Container
from src.domain.entities.workflow import Workflow, WorkflowStep
from src.domain.exceptions import WorkflowNotFoundError
from src.domain.ports.outbound.orchestrator_port import OrchestratorPort

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/workflows", tags=["Workflows"])


# In-memory storage (간단한 구현 - Step 15 목적)
# 실제 프로덕션에서는 DB 저장 필요
_workflows: dict[str, Workflow] = {}


@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(request: CreateWorkflowRequest):
    """
    Workflow 생성

    Args:
        request: Workflow 생성 요청

    Returns:
        생성된 Workflow 정보

    Raises:
        422: workflow_type이 'sequential' 또는 'parallel'이 아닌 경우
    """
    # Validate workflow_type
    if request.workflow_type not in ["sequential", "parallel"]:
        raise HTTPException(
            status_code=422,
            detail="workflow_type must be 'sequential' or 'parallel'",
        )

    # Create Workflow entity
    workflow_id = str(uuid4())
    workflow = Workflow(
        id=workflow_id,
        name=request.name,
        workflow_type=request.workflow_type,
        description=request.description,
        steps=[
            WorkflowStep(
                agent_endpoint_id=step.agent_endpoint_id,
                output_key=step.output_key,
                instruction=step.instruction,
            )
            for step in request.steps
        ],
    )

    # Store in-memory
    _workflows[workflow_id] = workflow

    logger.info(
        f"Workflow created: {workflow_id} ({request.workflow_type}, {len(request.steps)} steps)"
    )

    # Return response
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        workflow_type=workflow.workflow_type,
        description=workflow.description,
        steps=[
            WorkflowStepSchema(
                agent_endpoint_id=step.agent_endpoint_id,
                output_key=step.output_key,
                instruction=step.instruction,
            )
            for step in workflow.steps
        ],
        created_at=workflow.created_at.isoformat(),
    )


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows():
    """
    Workflow 목록 조회

    Returns:
        모든 Workflow 목록
    """
    return [
        WorkflowResponse(
            id=wf.id,
            name=wf.name,
            workflow_type=wf.workflow_type,
            description=wf.description,
            steps=[
                WorkflowStepSchema(
                    agent_endpoint_id=step.agent_endpoint_id,
                    output_key=step.output_key,
                    instruction=step.instruction,
                )
                for step in wf.steps
            ],
            created_at=wf.created_at.isoformat(),
        )
        for wf in _workflows.values()
    ]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """
    Workflow 상세 조회

    Args:
        workflow_id: Workflow ID

    Returns:
        Workflow 상세 정보

    Raises:
        404: Workflow가 존재하지 않는 경우
    """
    workflow = _workflows.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        workflow_type=workflow.workflow_type,
        description=workflow.description,
        steps=[
            WorkflowStepSchema(
                agent_endpoint_id=step.agent_endpoint_id,
                output_key=step.output_key,
                instruction=step.instruction,
            )
            for step in workflow.steps
        ],
        created_at=workflow.created_at.isoformat(),
    )


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(workflow_id: str):
    """
    Workflow 삭제

    Args:
        workflow_id: Workflow ID

    Raises:
        404: Workflow가 존재하지 않는 경우
    """
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    del _workflows[workflow_id]
    logger.info(f"Workflow deleted: {workflow_id}")


@router.post("/{workflow_id}/execute")
@inject
async def execute_workflow(
    workflow_id: str,
    request: ExecuteWorkflowRequest,
    http_request: Request,
    orchestrator: OrchestratorPort = Depends(Provide[Container.orchestrator_adapter]),
):
    """
    Workflow 실행 (SSE 스트리밍)

    Args:
        workflow_id: Workflow ID
        request: 실행 요청 (message, conversation_id)
        http_request: FastAPI Request 객체
        orchestrator: OrchestratorPort

    Returns:
        SSE 스트리밍 응답 (workflow_start, workflow_step_start, workflow_step_complete, workflow_complete, done)

    Raises:
        404: Workflow가 존재하지 않는 경우
    """
    # Check if workflow exists
    workflow = _workflows.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Create workflow agent
    await orchestrator.create_workflow_agent(workflow)

    # Execute workflow
    async def generate():
        try:
            # Generate conversation_id if not provided
            conversation_id = request.conversation_id or str(uuid4())

            async for chunk in orchestrator.execute_workflow(
                workflow_id=workflow_id,
                message=request.message,
                conversation_id=conversation_id,
            ):
                # Check if client disconnected (Zombie Task 방지)
                if await http_request.is_disconnected():
                    logger.info(f"Client disconnected, stopping workflow execution: {workflow_id}")
                    break

                # Convert StreamChunk to SSE event
                event_data = {
                    "type": chunk.event_type,
                    "workflow_id": workflow_id,
                }

                # Add event-specific data
                if chunk.content:
                    event_data["content"] = chunk.content
                if chunk.metadata:
                    event_data.update(chunk.metadata)

                yield f"data: {json.dumps(event_data)}\n\n"

            # Send done event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except WorkflowNotFoundError as e:
            logger.error(f"Workflow not found during execution: {e}")
            error_data = {
                "type": "error",
                "code": "WORKFLOW_NOT_FOUND",
                "message": str(e),
            }
            yield f"data: {json.dumps(error_data)}\n\n"

        except Exception as e:
            logger.error(f"Workflow execution error: {e}", exc_info=True)
            error_data = {
                "type": "error",
                "code": "WORKFLOW_EXECUTION_ERROR",
                "message": str(e),
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
