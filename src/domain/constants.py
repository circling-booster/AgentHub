"""Domain Constants - 도메인 상수 정의

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""


class ErrorCode:
    """에러 코드 상수 (Backend ↔ Extension 공유)

    Extension의 TypeScript enum과 동일한 값을 사용하여 타입 안전성을 보장합니다.
    문자열 하드코딩을 방지하고 IDE 자동완성을 지원합니다.
    """

    # LLM 관련 에러
    LLM_RATE_LIMIT = "LlmRateLimitError"
    LLM_AUTHENTICATION = "LlmAuthenticationError"

    # Endpoint 관련 에러
    ENDPOINT_CONNECTION = "EndpointConnectionError"
    ENDPOINT_TIMEOUT = "EndpointTimeoutError"
    ENDPOINT_NOT_FOUND = "EndpointNotFoundError"

    # Tool 관련 에러
    TOOL_NOT_FOUND = "ToolNotFoundError"

    # Conversation 관련 에러
    CONVERSATION_NOT_FOUND = "ConversationNotFoundError"

    # Validation 관련 에러
    INVALID_URL = "InvalidUrlError"

    # Workflow 관련 에러
    WORKFLOW_NOT_FOUND = "WorkflowNotFoundError"

    # 기타
    UNKNOWN = "UnknownError"
