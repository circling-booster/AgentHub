"""Workflow Management API Schemas

Workflow 생성/조회/실행 Request/Response 모델
"""

from pydantic import BaseModel, Field


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


class ExecuteWorkflowRequest(BaseModel):
    """Workflow 실행 요청"""

    message: str = Field(..., description="사용자 메시지")
    conversation_id: str | None = Field(default=None, description="대화 세션 ID (선택)")
