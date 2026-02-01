"""StreamChunk - SSE 스트리밍 이벤트 엔티티

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class StreamChunk:
    """
    SSE 스트리밍 이벤트 단위

    LLM 응답, 도구 호출, 에이전트 전환, 워크플로우 등 다양한 이벤트 타입을 표현합니다.
    frozen=True로 불변성을 보장하여 안전한 스트리밍을 지원합니다.

    Attributes:
        type: 이벤트 타입 ("text", "tool_call", "tool_result", "agent_transfer",
              "workflow_start", "workflow_step_start", "workflow_step_complete",
              "workflow_complete", "error", "done")
        content: 텍스트 콘텐츠 (type="text", "error")
        tool_name: 도구 이름 (type="tool_call", "tool_result")
        tool_arguments: 도구 인자 dict (type="tool_call")
        result: 도구 실행 결과 (type="tool_result")
        agent_name: 에이전트 이름 (type="agent_transfer", "workflow_step_start", "workflow_step_complete")
        error_code: 에러 코드 (type="error")
        workflow_id: 워크플로우 ID (workflow events)
        workflow_type: 워크플로우 타입 (type="workflow_start")
        workflow_status: 워크플로우 상태 (type="workflow_complete")
        step_number: 스텝 번호 (type="workflow_step_start", "workflow_step_complete")
        total_steps: 전체 스텝 수 (type="workflow_start", "workflow_complete")
    """

    type: str
    content: str = ""
    tool_name: str = ""
    tool_arguments: dict[str, Any] = field(default_factory=dict)
    result: str = ""
    agent_name: str = ""
    error_code: str = ""
    # Workflow-related fields
    workflow_id: str = ""
    workflow_type: str = ""
    workflow_status: str = ""
    step_number: int = 0
    total_steps: int = 0

    @staticmethod
    def text(content: str) -> "StreamChunk":
        """텍스트 청크 생성"""
        return StreamChunk(type="text", content=content)

    @staticmethod
    def tool_call(name: str, arguments: dict[str, Any]) -> "StreamChunk":
        """도구 호출 청크 생성"""
        return StreamChunk(type="tool_call", tool_name=name, tool_arguments=arguments)

    @staticmethod
    def tool_result(name: str, result: str) -> "StreamChunk":
        """도구 결과 청크 생성"""
        return StreamChunk(type="tool_result", tool_name=name, result=result)

    @staticmethod
    def agent_transfer(agent_name: str) -> "StreamChunk":
        """에이전트 전환 청크 생성"""
        return StreamChunk(type="agent_transfer", agent_name=agent_name)

    @staticmethod
    def done() -> "StreamChunk":
        """완료 청크 생성"""
        return StreamChunk(type="done")

    @staticmethod
    def error(message: str, code: str = "") -> "StreamChunk":
        """에러 청크 생성"""
        return StreamChunk(type="error", content=message, error_code=code)

    @staticmethod
    def workflow_start(workflow_id: str, workflow_type: str, total_steps: int) -> "StreamChunk":
        """워크플로우 시작 청크 생성"""
        return StreamChunk(
            type="workflow_start",
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            total_steps=total_steps,
        )

    @staticmethod
    def workflow_step_start(workflow_id: str, step_number: int, agent_name: str) -> "StreamChunk":
        """워크플로우 스텝 시작 청크 생성"""
        return StreamChunk(
            type="workflow_step_start",
            workflow_id=workflow_id,
            step_number=step_number,
            agent_name=agent_name,
        )

    @staticmethod
    def workflow_step_complete(
        workflow_id: str, step_number: int, agent_name: str
    ) -> "StreamChunk":
        """워크플로우 스텝 완료 청크 생성"""
        return StreamChunk(
            type="workflow_step_complete",
            workflow_id=workflow_id,
            step_number=step_number,
            agent_name=agent_name,
        )

    @staticmethod
    def workflow_complete(workflow_id: str, status: str, total_steps: int) -> "StreamChunk":
        """워크플로우 완료 청크 생성"""
        return StreamChunk(
            type="workflow_complete",
            workflow_id=workflow_id,
            workflow_status=status,
            total_steps=total_steps,
        )
