"""Error Code Constants 테스트 - Step 0: Part B

ErrorCode 클래스가 정의하는 상수들이 Backend ↔ Extension 간 일치하는지 검증
"""

import pytest


def test_error_code_constants_exist():
    """ErrorCode 클래스에 필수 상수들이 정의되어 있는지 확인"""
    from domain.constants import ErrorCode

    # 필수 에러 코드 검증
    assert hasattr(ErrorCode, "LLM_RATE_LIMIT")
    assert hasattr(ErrorCode, "LLM_AUTHENTICATION")
    assert hasattr(ErrorCode, "ENDPOINT_CONNECTION")
    assert hasattr(ErrorCode, "ENDPOINT_TIMEOUT")
    assert hasattr(ErrorCode, "ENDPOINT_NOT_FOUND")
    assert hasattr(ErrorCode, "TOOL_NOT_FOUND")
    assert hasattr(ErrorCode, "CONVERSATION_NOT_FOUND")
    assert hasattr(ErrorCode, "INVALID_URL")
    assert hasattr(ErrorCode, "UNKNOWN")

    # 상수 값 검증 (Extension TypeScript enum과 일치해야 함)
    assert ErrorCode.LLM_RATE_LIMIT == "LlmRateLimitError"
    assert ErrorCode.LLM_AUTHENTICATION == "LlmAuthenticationError"
    assert ErrorCode.ENDPOINT_CONNECTION == "EndpointConnectionError"
    assert ErrorCode.ENDPOINT_TIMEOUT == "EndpointTimeoutError"
    assert ErrorCode.ENDPOINT_NOT_FOUND == "EndpointNotFoundError"
    assert ErrorCode.TOOL_NOT_FOUND == "ToolNotFoundError"
    assert ErrorCode.CONVERSATION_NOT_FOUND == "ConversationNotFoundError"
    assert ErrorCode.INVALID_URL == "InvalidUrlError"
    assert ErrorCode.UNKNOWN == "UnknownError"


def test_exception_uses_error_code_constant():
    """DomainException 서브클래스들이 ErrorCode 상수를 사용하는지 확인"""
    from domain.constants import ErrorCode
    from domain.exceptions import (
        ConversationNotFoundError,
        EndpointConnectionError,
        EndpointNotFoundError,
        EndpointTimeoutError,
        InvalidUrlError,
        LlmAuthenticationError,
        LlmRateLimitError,
        ToolNotFoundError,
    )

    # 각 예외가 올바른 ErrorCode 상수를 사용하는지 검증
    error = LlmRateLimitError("test")
    assert error.code == ErrorCode.LLM_RATE_LIMIT

    error = LlmAuthenticationError("test")
    assert error.code == ErrorCode.LLM_AUTHENTICATION

    error = EndpointConnectionError("test")
    assert error.code == ErrorCode.ENDPOINT_CONNECTION

    error = EndpointTimeoutError("test")
    assert error.code == ErrorCode.ENDPOINT_TIMEOUT

    error = EndpointNotFoundError("test")
    assert error.code == ErrorCode.ENDPOINT_NOT_FOUND

    error = ToolNotFoundError("test")
    assert error.code == ErrorCode.TOOL_NOT_FOUND

    error = ConversationNotFoundError("test")
    assert error.code == ErrorCode.CONVERSATION_NOT_FOUND

    error = InvalidUrlError("test")
    assert error.code == ErrorCode.INVALID_URL


def test_error_code_prevents_typos():
    """ErrorCode 상수를 사용하면 오타를 방지할 수 있음을 검증"""
    from domain.constants import ErrorCode

    # ErrorCode를 통해 접근하면 IDE 자동완성 지원
    # 존재하지 않는 속성 접근 시 AttributeError 발생
    with pytest.raises(AttributeError):
        _ = ErrorCode.INVALID_TYPO  # type: ignore
