"""Chat API Request/Response Schemas"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """채팅 스트리밍 요청"""

    conversation_id: str | None = None
    message: str = Field(..., min_length=1)


class ChatStreamEvent(BaseModel):
    """SSE 스트리밍 이벤트"""

    type: str  # "text", "tool_call", "tool_result", "done", "error"
    content: str | None = None
    name: str | None = None  # tool_call용
    arguments: dict | None = None  # tool_call용
    result: dict | None = None  # tool_result용
    message: str | None = None  # error용
