"""ElicitationRequest 엔티티 테스트

TDD로 작성됨:
- ElicitationRequest
- ElicitationAction
- ElicitationStatus
"""

from src.domain.entities.elicitation_request import (
    ElicitationAction,
    ElicitationRequest,
    ElicitationStatus,
)


class TestElicitationRequest:
    def test_create_pending_request(self):
        """대기 중인 요청 생성"""
        request = ElicitationRequest(
            id="req-456",
            endpoint_id="mcp-server-1",
            message="Enter API key",
            requested_schema={"type": "object", "properties": {"api_key": {"type": "string"}}},
        )
        assert request.status == ElicitationStatus.PENDING
        assert request.action is None
        assert request.content is None

    def test_accept_action(self):
        """accept 액션 설정"""
        request = ElicitationRequest(
            id="req-456",
            endpoint_id="mcp-server-1",
            message="Enter API key",
            requested_schema={},
            action=ElicitationAction.ACCEPT,
            content={"api_key": "sk-xxx"},
        )
        assert request.action == ElicitationAction.ACCEPT
        assert request.content == {"api_key": "sk-xxx"}

    def test_decline_action(self):
        """decline 액션 설정"""
        request = ElicitationRequest(
            id="req-456",
            endpoint_id="mcp-server-1",
            message="Enter API key",
            requested_schema={},
            action=ElicitationAction.DECLINE,
        )
        assert request.action == ElicitationAction.DECLINE
