"""Domain Exceptions - 도메인 예외 정의

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""


class DomainException(Exception):
    """도메인 예외 기본 클래스"""

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__


# ============================================================
# Endpoint 관련 예외
# ============================================================


class EndpointNotFoundError(DomainException):
    """엔드포인트를 찾을 수 없음"""

    pass


class DuplicateEndpointError(DomainException):
    """이미 등록된 엔드포인트"""

    pass


class EndpointConnectionError(DomainException):
    """엔드포인트 연결 실패"""

    pass


class EndpointTimeoutError(DomainException):
    """엔드포인트 응답 시간 초과"""

    pass


# ============================================================
# Tool 관련 예외
# ============================================================


class ToolNotFoundError(DomainException):
    """도구를 찾을 수 없음"""

    pass


class ToolExecutionError(DomainException):
    """도구 실행 실패"""

    pass


class ToolLimitExceededError(DomainException):
    """활성 도구 수가 제한을 초과함"""

    pass


# ============================================================
# LLM 관련 예외
# ============================================================


class LlmRateLimitError(DomainException):
    """LLM API Rate Limit 초과"""

    pass


class LlmAuthenticationError(DomainException):
    """LLM API 인증 실패"""

    pass


# ============================================================
# Conversation 관련 예외
# ============================================================


class ConversationNotFoundError(DomainException):
    """대화를 찾을 수 없음"""

    pass


# ============================================================
# Validation 관련 예외
# ============================================================


class InvalidUrlError(DomainException):
    """유효하지 않은 URL"""

    pass


class ValidationError(DomainException):
    """입력 검증 실패"""

    pass
