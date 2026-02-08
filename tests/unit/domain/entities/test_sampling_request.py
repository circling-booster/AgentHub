"""SamplingRequest 엔티티 테스트

TDD로 작성됨:
- SamplingRequest
- SamplingStatus
"""

from datetime import datetime

from src.domain.entities.sampling_request import SamplingRequest, SamplingStatus


class TestSamplingRequest:
    def test_create_pending_request(self):
        """대기 중인 요청 생성"""
        request = SamplingRequest(
            id="req-123",
            endpoint_id="mcp-server-1",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1024,
        )
        assert request.status == SamplingStatus.PENDING
        assert request.llm_result is None
        assert isinstance(request.created_at, datetime)

    def test_create_with_optional_fields(self):
        """선택 필드 포함 생성"""
        request = SamplingRequest(
            id="req-123",
            endpoint_id="mcp-server-1",
            messages=[{"role": "user", "content": "test"}],
            model_preferences={"model": "gpt-4"},
            system_prompt="You are helpful",
            max_tokens=2048,
        )
        assert request.model_preferences == {"model": "gpt-4"}
        assert request.system_prompt == "You are helpful"
        assert request.max_tokens == 2048

    def test_datetime_uses_timezone_aware(self):
        """datetime이 timezone-aware인지 확인"""
        request = SamplingRequest(
            id="req-123",
            endpoint_id="mcp-server-1",
            messages=[],
        )
        assert request.created_at.tzinfo is not None

    def test_rejection_reason_defaults_empty(self):
        """거부 사유가 기본값으로 빈 문자열인지 확인"""
        request = SamplingRequest(
            id="req-123",
            endpoint_id="mcp-server-1",
            messages=[{"role": "user", "content": "test"}],
        )
        assert request.rejection_reason == ""
