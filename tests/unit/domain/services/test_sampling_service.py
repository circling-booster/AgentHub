"""SamplingService 테스트 (TDD - Method C Signal 패턴)

asyncio.Event를 사용한 Signal 패턴 테스트.
"""

import asyncio

import pytest

from src.domain.entities.sampling_request import SamplingRequest, SamplingStatus
from src.domain.services.sampling_service import SamplingService


@pytest.fixture
def sampling_service():
    """SamplingService 픽스처"""
    return SamplingService()


class TestSamplingService:
    """SamplingService 테스트 (Method C Signal 패턴)"""

    async def test_create_request_stores_in_pending(self, sampling_service):
        """요청 생성 시 pending 목록에 추가"""
        # Given: 새 요청 생성
        request = SamplingRequest(
            id="req-1",
            endpoint_id="ep-1",
            messages=[{"role": "user", "content": "Hello"}],
        )

        # When: 요청 생성
        await sampling_service.create_request(request)

        # Then: pending 목록에 추가됨
        pending = sampling_service.list_pending()
        assert len(pending) == 1
        assert pending[0].id == "req-1"
        assert pending[0].status == SamplingStatus.PENDING

    async def test_get_request_returns_request(self, sampling_service):
        """get_request() - 요청 조회"""
        # Given: 요청 생성
        request = SamplingRequest(
            id="req-1",
            endpoint_id="ep-1",
            messages=[{"role": "user", "content": "Hello"}],
        )
        await sampling_service.create_request(request)

        # When: 요청 조회
        result = sampling_service.get_request("req-1")

        # Then: 요청 반환
        assert result is not None
        assert result.id == "req-1"

    async def test_get_request_returns_none_for_unknown(self, sampling_service):
        """get_request() - 존재하지 않는 요청 → None"""
        # When: 존재하지 않는 요청 조회
        result = sampling_service.get_request("nonexistent")

        # Then: None 반환
        assert result is None

    async def test_list_pending_returns_only_pending(self, sampling_service):
        """list_pending() - PENDING 상태만 반환"""
        # Given: 여러 상태의 요청 생성
        req1 = SamplingRequest(
            id="req-1",
            endpoint_id="ep-1",
            messages=[{"role": "user", "content": "Hello"}],
        )
        req2 = SamplingRequest(
            id="req-2",
            endpoint_id="ep-1",
            messages=[{"role": "user", "content": "World"}],
        )
        await sampling_service.create_request(req1)
        await sampling_service.create_request(req2)

        # When: req-1을 승인
        await sampling_service.approve("req-1", {"content": "test"})

        # Then: pending 목록에는 req-2만 남음
        pending = sampling_service.list_pending()
        assert len(pending) == 1
        assert pending[0].id == "req-2"

    async def test_approve_signals_event(self, sampling_service):
        """approve() - asyncio.Event 시그널"""
        # Given: 요청 생성
        request = SamplingRequest(
            id="req-1",
            endpoint_id="ep-1",
            messages=[{"role": "user", "content": "Hello"}],
        )
        await sampling_service.create_request(request)

        # When: 요청 승인
        success = await sampling_service.approve("req-1", {"content": "LLM response"})

        # Then: 승인 성공 및 상태 변경
        assert success is True
        result = sampling_service.get_request("req-1")
        assert result is not None
        assert result.status == SamplingStatus.APPROVED
        assert result.llm_result == {"content": "LLM response"}

    async def test_wait_for_response_returns_after_signal(self, sampling_service):
        """wait_for_response() - 시그널 후 즉시 반환"""
        # Given: 요청 생성
        request = SamplingRequest(
            id="req-1",
            endpoint_id="ep-1",
            messages=[{"role": "user", "content": "Hello"}],
        )
        await sampling_service.create_request(request)

        # Background task: 1초 후 approve
        async def delayed_approve():
            await asyncio.sleep(1.0)
            await sampling_service.approve("req-1", {"content": "test"})

        asyncio.create_task(delayed_approve())

        # When: 30초 타임아웃이지만 1초 내 반환됨
        result = await sampling_service.wait_for_response("req-1", timeout=30.0)

        # Then: 승인된 결과 반환
        assert result is not None
        assert result.status == SamplingStatus.APPROVED
        assert result.llm_result == {"content": "test"}

    async def test_wait_for_response_timeout(self, sampling_service):
        """wait_for_response() - timeout → None"""
        # Given: 요청 생성
        request = SamplingRequest(
            id="req-1",
            endpoint_id="ep-1",
            messages=[{"role": "user", "content": "Hello"}],
        )
        await sampling_service.create_request(request)

        # When: 0.1초 timeout (approve 없이)
        result = await sampling_service.wait_for_response("req-1", timeout=0.1)

        # Then: Timeout (None 반환)
        assert result is None

    async def test_reject_sets_status(self, sampling_service):
        """reject() - 상태 REJECTED로 변경"""
        # Given: 요청 생성
        request = SamplingRequest(
            id="req-1",
            endpoint_id="ep-1",
            messages=[{"role": "user", "content": "Hello"}],
        )
        await sampling_service.create_request(request)

        # When: 요청 거부
        success = await sampling_service.reject("req-1", reason="Not authorized")

        # Then: 거부 성공 및 상태 변경
        assert success is True
        result = sampling_service.get_request("req-1")
        assert result is not None
        assert result.status == SamplingStatus.REJECTED
        assert result.rejection_reason == "Not authorized"

    async def test_cleanup_expired_removes_old_requests(self, sampling_service):
        """cleanup_expired() - TTL 초과 요청 제거"""
        # Given: TTL 1초로 설정한 서비스
        service = SamplingService(ttl_seconds=1)
        request = SamplingRequest(
            id="req-1",
            endpoint_id="ep-1",
            messages=[{"role": "user", "content": "Hello"}],
        )
        await service.create_request(request)

        # When: 1.5초 대기 후 cleanup
        await asyncio.sleep(1.5)
        removed = await service.cleanup_expired()

        # Then: 요청 제거됨
        assert removed == 1
        assert service.get_request("req-1") is None

    async def test_wait_for_response_unknown_request(self, sampling_service):
        """wait_for_response() - 존재하지 않는 요청 → None"""
        # When: 존재하지 않는 요청 대기
        result = await sampling_service.wait_for_response("nonexistent", timeout=0.1)

        # Then: None 반환
        assert result is None

    async def test_approve_unknown_request(self, sampling_service):
        """approve() - 존재하지 않는 요청 → False"""
        # When: 존재하지 않는 요청 승인
        success = await sampling_service.approve("nonexistent", {"content": "test"})

        # Then: False 반환
        assert success is False

    async def test_reject_unknown_request(self, sampling_service):
        """reject() - 존재하지 않는 요청 → False"""
        # When: 존재하지 않는 요청 거부
        success = await sampling_service.reject("nonexistent")

        # Then: False 반환
        assert success is False
