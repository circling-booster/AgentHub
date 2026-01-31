"""Chat API Request/Response Schemas"""

from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.stream_chunk import StreamChunk


class ChatRequest(BaseModel):
    """채팅 스트리밍 요청"""

    conversation_id: str | None = None
    message: str = Field(..., min_length=1)


class ChatStreamEvent(BaseModel):
    """SSE 스트리밍 이벤트 (StreamChunk → JSON 직렬화)"""

    type: str  # "text", "tool_call", "tool_result", "agent_transfer", "done", "error"
    content: str | None = None  # text, error
    tool_name: str | None = None  # tool_call, tool_result
    tool_arguments: dict[str, Any] | None = None  # tool_call
    result: str | None = None  # tool_result
    agent_name: str | None = None  # agent_transfer
    error_code: str | None = None  # error

    @classmethod
    def from_stream_chunk(cls, chunk: StreamChunk) -> "ChatStreamEvent":
        """StreamChunk를 HTTP 응답 이벤트로 변환"""
        return cls(
            type=chunk.type,
            content=chunk.content or None,
            tool_name=chunk.tool_name or None,
            tool_arguments=chunk.tool_arguments or None,
            result=chunk.result or None,
            agent_name=chunk.agent_name or None,
            error_code=chunk.error_code or None,
        )
