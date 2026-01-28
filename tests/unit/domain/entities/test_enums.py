"""Domain Enums 테스트 - MessageRole, EndpointType, EndpointStatus"""

import pytest

from src.domain.entities.enums import EndpointStatus, EndpointType, MessageRole


class TestMessageRole:
    """MessageRole 열거형 테스트"""

    def test_message_role_values(self):
        """MessageRole 값 확인"""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.TOOL.value == "tool"

    def test_message_role_is_string(self):
        """MessageRole은 str을 상속하여 문자열로 사용 가능"""
        assert isinstance(MessageRole.USER, str)
        assert MessageRole.USER == "user"

    def test_message_role_from_string(self):
        """문자열에서 MessageRole 생성"""
        assert MessageRole("user") == MessageRole.USER
        assert MessageRole("assistant") == MessageRole.ASSISTANT


class TestEndpointType:
    """EndpointType 열거형 테스트"""

    def test_endpoint_type_values(self):
        """EndpointType 값 확인"""
        assert EndpointType.MCP.value == "mcp"
        assert EndpointType.A2A.value == "a2a"

    def test_endpoint_type_is_string(self):
        """EndpointType은 str을 상속하여 문자열로 사용 가능"""
        assert isinstance(EndpointType.MCP, str)
        assert EndpointType.MCP == "mcp"

    def test_endpoint_type_from_string(self):
        """문자열에서 EndpointType 생성"""
        assert EndpointType("mcp") == EndpointType.MCP
        assert EndpointType("a2a") == EndpointType.A2A


class TestEndpointStatus:
    """EndpointStatus 열거형 테스트"""

    def test_endpoint_status_values(self):
        """EndpointStatus 값 확인"""
        assert EndpointStatus.CONNECTED.value == "connected"
        assert EndpointStatus.DISCONNECTED.value == "disconnected"
        assert EndpointStatus.ERROR.value == "error"
        assert EndpointStatus.UNKNOWN.value == "unknown"

    def test_endpoint_status_is_string(self):
        """EndpointStatus은 str을 상속하여 문자열로 사용 가능"""
        assert isinstance(EndpointStatus.CONNECTED, str)
        assert EndpointStatus.CONNECTED == "connected"

    def test_endpoint_status_from_string(self):
        """문자열에서 EndpointStatus 생성"""
        assert EndpointStatus("connected") == EndpointStatus.CONNECTED
        assert EndpointStatus("error") == EndpointStatus.ERROR

    def test_invalid_status_raises_error(self):
        """유효하지 않은 상태 문자열은 에러"""
        with pytest.raises(ValueError):
            EndpointStatus("invalid_status")
