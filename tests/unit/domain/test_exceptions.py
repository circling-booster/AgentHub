"""Domain Exceptions 테스트"""

import pytest

from src.domain.constants import ErrorCode
from src.domain.exceptions import (
    DomainException,
    EndpointNotFoundError,
    HitlRequestNotFoundError,
    HitlTimeoutError,
    PromptNotFoundError,
    ResourceNotFoundError,
    ToolNotFoundError,
    ValidationError,
)


class TestDomainException:
    """DomainException 기본 클래스 테스트"""

    def test_create_with_message(self):
        """메시지로 예외 생성"""
        # When
        exc = DomainException("Something went wrong")

        # Then
        assert exc.message == "Something went wrong"
        assert exc.code == "DomainException"
        assert str(exc) == "Something went wrong"

    def test_create_with_custom_code(self):
        """커스텀 코드로 예외 생성"""
        # When
        exc = DomainException("Error occurred", code="CUSTOM_ERROR")

        # Then
        assert exc.message == "Error occurred"
        assert exc.code == "CUSTOM_ERROR"


class TestSpecificExceptions:
    """특정 도메인 예외 테스트"""

    def test_endpoint_not_found_error(self):
        """EndpointNotFoundError 테스트"""
        # When
        exc = EndpointNotFoundError("Endpoint 'abc' not found")

        # Then
        assert exc.message == "Endpoint 'abc' not found"
        assert exc.code == "EndpointNotFoundError"
        assert isinstance(exc, DomainException)

    def test_tool_not_found_error(self):
        """ToolNotFoundError 테스트"""
        # When
        exc = ToolNotFoundError("Tool 'search' not found")

        # Then
        assert exc.message == "Tool 'search' not found"
        assert isinstance(exc, DomainException)

    def test_validation_error(self):
        """ValidationError 테스트"""
        # When
        exc = ValidationError("Invalid input")

        # Then
        assert exc.message == "Invalid input"
        assert isinstance(exc, DomainException)

    def test_exception_can_be_raised_and_caught(self):
        """예외를 raise하고 catch할 수 있음"""
        # When / Then
        with pytest.raises(EndpointNotFoundError) as exc_info:
            raise EndpointNotFoundError("Not found")

        assert exc_info.value.message == "Not found"


class TestHitlExceptions:
    """HITL 관련 예외 테스트"""

    def test_hitl_timeout_error(self):
        """HITL 타임아웃 에러"""
        error = HitlTimeoutError("Request timed out")
        assert error.message == "Request timed out"
        assert error.code == ErrorCode.HITL_TIMEOUT

    def test_hitl_request_not_found_error(self):
        """HITL 요청 미발견 에러"""
        error = HitlRequestNotFoundError("Request not found")
        assert error.code == ErrorCode.HITL_REQUEST_NOT_FOUND


class TestResourceExceptions:
    """Resource/Prompt 관련 예외 테스트"""

    def test_resource_not_found_error(self):
        """리소스 미발견 에러"""
        error = ResourceNotFoundError("Resource not found")
        assert error.code == ErrorCode.RESOURCE_NOT_FOUND

    def test_prompt_not_found_error(self):
        """프롬프트 미발견 에러"""
        error = PromptNotFoundError("Prompt not found")
        assert error.code == ErrorCode.PROMPT_NOT_FOUND
