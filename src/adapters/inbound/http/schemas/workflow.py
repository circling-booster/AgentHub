"""Workflow Management API Schemas

Workflow 생성/조회/실행 Request/Response 모델
"""

from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.stream_chunk import StreamChunk


class WorkflowStepSchema(BaseModel):
    """Workflow Step 스키마"""

    agent_endpoint_id: str = Field(..., description="등록된 A2A 에이전트 엔드포인트 ID")
    output_key: str = Field(..., description="이 Step 결과를 저장할 session.state 키")
    instruction: str = Field(default="", description="Step 특화 instruction (선택)")


class CreateWorkflowRequest(BaseModel):
    """Workflow 생성 요청"""

    name: str = Field(..., description="Workflow 이름")
    workflow_type: str = Field(..., description="실행 방식: 'sequential' 또는 'parallel'")
    description: str = Field(default="", description="Workflow 설명")
    steps: list[WorkflowStepSchema] = Field(..., description="실행할 Step 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Echo then Math",
                "workflow_type": "sequential",
                "description": "Echo user message then calculate",
                "steps": [
                    {
                        "agent_endpoint_id": "echo-agent-id",
                        "output_key": "echo_result",
                        "instruction": "Echo the user message",
                    },
                    {
                        "agent_endpoint_id": "math-agent-id",
                        "output_key": "math_result",
                        "instruction": "Calculate sum of 1+1",
                    },
                ],
            }
        }


class WorkflowResponse(BaseModel):
    """Workflow 응답"""

    id: str
    name: str
    workflow_type: str
    description: str
    steps: list[WorkflowStepSchema]
    created_at: str


class WorkflowStreamEvent(BaseModel):
    """Workflow SSE 스트리밍 이벤트 (StreamChunk → JSON 직렬화)"""

    type: str  # "workflow_start", "workflow_step_start", "workflow_step_complete", "workflow_complete", "text", "tool_call", "tool_result", "error"
    workflow_id: str
    content: str | None = None  # text, error
    tool_name: str | None = None  # tool_call, tool_result
    tool_arguments: dict[str, Any] | None = None  # tool_call
    result: str | None = None  # tool_result
    agent_name: str | None = None  # workflow_step_start, workflow_step_complete
    error_code: str | None = None  # error
    workflow_type: str | None = None  # workflow_start
    workflow_status: str | None = None  # workflow_complete
    step_number: int | None = None  # workflow_step_start, workflow_step_complete
    total_steps: int | None = None  # workflow_start, workflow_complete

    @classmethod
    def from_stream_chunk(cls, chunk: StreamChunk, workflow_id: str) -> "WorkflowStreamEvent":
        """StreamChunk를 Workflow HTTP 응답 이벤트로 변환"""
        return cls(
            type=chunk.type,
            workflow_id=workflow_id,
            content=chunk.content or None,
            tool_name=chunk.tool_name or None,
            tool_arguments=chunk.tool_arguments or None,
            result=chunk.result or None,
            agent_name=chunk.agent_name or None,
            error_code=chunk.error_code or None,
            workflow_type=chunk.workflow_type or None,
            workflow_status=chunk.workflow_status or None,
            step_number=chunk.step_number if chunk.step_number > 0 else None,
            total_steps=chunk.total_steps if chunk.total_steps > 0 else None,
        )


class ExecuteWorkflowRequest(BaseModel):
    """Workflow 실행 요청"""

    message: str = Field(..., description="사용자 메시지")
    conversation_id: str | None = Field(default=None, description="대화 세션 ID (선택)")
