"""ElicitationService 테스트 (TDD - Signal 패턴)

asyncio.Event를 사용한 Signal 패턴 테스트.
SamplingService와 동일한 패턴 사용.
"""

import asyncio

import pytest

from src.domain.entities.elicitation_request import (
    ElicitationAction,
    ElicitationRequest,
    ElicitationStatus,
)
from src.domain.services.elicitation_service import ElicitationService


@pytest.fixture
def elicitation_service():
    """ElicitationService 픽스처"""
    return ElicitationService()


class TestElicitationService:
    """ElicitationService 테스트 (Signal 패턴)"""

    async def test_create_request_stores_in_pending(self, elicitation_service):
        """요청 생성 시 pending 목록에 추가"""
        # Given: 새 요청 생성
        request = ElicitationRequest(
            id="req-1",
            endpoint_id="ep-1",
            message="Enter API key",
            requested_schema={"type": "object", "properties": {"api_key": {"type": "string"}}},
        )

        # When: 요청 생성
        await elicitation_service.create_request(request)

        # Then: pending 목록에 추가됨
        pending = elicitation_service.list_pending()
        assert len(pending) == 1
        assert pending[0].id == "req-1"
        assert pending[0].status == ElicitationStatus.PENDING

    async def test_respond_accept_with_content(self, elicitation_service):
        """respond(ACCEPT) - content 저장"""
        # Given: 요청 생성
        request = ElicitationRequest(
            id="req-1",
            endpoint_id="ep-1",
            message="Enter API key",
            requested_schema={},
        )
        await elicitation_service.create_request(request)

        # When: ACCEPT 응답
        success = await elicitation_service.respond(
            "req-1",
            ElicitationAction.ACCEPT,
            content={"api_key": "sk-xxx"},
        )

        # Then: 승인 성공 및 상태 변경
        assert success is True
        result = elicitation_service.get_request("req-1")
        assert result is not None
        assert result.action == ElicitationAction.ACCEPT
        assert result.status == ElicitationStatus.ACCEPTED
        assert result.content == {"api_key": "sk-xxx"}

    async def test_respond_decline(self, elicitation_service):
        """respond(DECLINE)"""
        # Given: 요청 생성
        request = ElicitationRequest(
            id="req-1",
            endpoint_id="ep-1",
            message="Enter data",
            requested_schema={},
        )
        await elicitation_service.create_request(request)

        # When: DECLINE 응답
        success = await elicitation_service.respond(
            "req-1",
            ElicitationAction.DECLINE,
        )

        # Then: 거부 성공 및 상태 변경
        assert success is True
        result = elicitation_service.get_request("req-1")
        assert result is not None
        assert result.action == ElicitationAction.DECLINE
        assert result.status == ElicitationStatus.DECLINED

    async def test_respond_cancel(self, elicitation_service):
        """respond(CANCEL)"""
        # Given: 요청 생성
        request = ElicitationRequest(
            id="req-1",
            endpoint_id="ep-1",
            message="Enter data",
            requested_schema={},
        )
        await elicitation_service.create_request(request)

        # When: CANCEL 응답
        success = await elicitation_service.respond(
            "req-1",
            ElicitationAction.CANCEL,
        )

        # Then: 취소 성공 및 상태 변경
        assert success is True
        result = elicitation_service.get_request("req-1")
        assert result is not None
        assert result.action == ElicitationAction.CANCEL
        assert result.status == ElicitationStatus.CANCELLED

    async def test_wait_for_response_timeout(self, elicitation_service):
        """wait_for_response() - timeout"""
        # Given: 요청 생성
        request = ElicitationRequest(
            id="req-1",
            endpoint_id="ep-1",
            message="Enter data",
            requested_schema={},
        )
        await elicitation_service.create_request(request)

        # When: 0.1초 timeout (응답 없이)
        result = await elicitation_service.wait_for_response("req-1", timeout=0.1)

        # Then: Timeout (None 반환)
        assert result is None

    async def test_list_pending_returns_only_pending(self, elicitation_service):
        """list_pending() - PENDING 상태만 반환"""
        # Given: 여러 상태의 요청 생성
        pending_req = ElicitationRequest(
            id="req-pending",
            endpoint_id="ep-1",
            message="Enter data",
            requested_schema={"type": "object", "properties": {"data": {"type": "string"}}},
        )
        await elicitation_service.create_request(pending_req)

        accepted_req = ElicitationRequest(
            id="req-accepted",
            endpoint_id="ep-1",
            message="Enter data 2",
            requested_schema={"type": "object", "properties": {"data": {"type": "string"}}},
        )
        await elicitation_service.create_request(accepted_req)
        await elicitation_service.respond(
            "req-accepted", ElicitationAction.ACCEPT, content={"data": "value"}
        )

        # When: pending 목록 조회
        pending_list = elicitation_service.list_pending()

        # Then: pending만 반환
        assert len(pending_list) == 1
        assert pending_list[0].id == "req-pending"

    async def test_wait_for_response_returns_after_signal(self, elicitation_service):
        """wait_for_response() - 시그널 후 즉시 반환"""
        # Given: 요청 생성
        request = ElicitationRequest(
            id="req-1",
            endpoint_id="ep-1",
            message="Enter data",
            requested_schema={},
        )
        await elicitation_service.create_request(request)

        # Background task: 1초 후 respond
        async def delayed_respond():
            await asyncio.sleep(1.0)
            await elicitation_service.respond(
                "req-1",
                ElicitationAction.ACCEPT,
                content={"test": "value"},
            )

        asyncio.create_task(delayed_respond())

        # When: 30초 타임아웃이지만 1초 내 반환됨
        result = await elicitation_service.wait_for_response("req-1", timeout=30.0)

        # Then: 응답된 결과 반환
        assert result is not None
        assert result.status == ElicitationStatus.ACCEPTED
        assert result.content == {"test": "value"}

    async def test_cleanup_expired_removes_old_requests(self, elicitation_service):
        """cleanup_expired() - TTL 초과 요청 제거"""
        # Given: TTL 1초로 설정한 서비스
        service = ElicitationService(ttl_seconds=1)
        request = ElicitationRequest(
            id="req-1",
            endpoint_id="ep-1",
            message="Enter data",
            requested_schema={},
        )
        await service.create_request(request)

        # When: 1.5초 대기 후 cleanup
        await asyncio.sleep(1.5)
        removed = await service.cleanup_expired()

        # Then: 요청 제거됨
        assert removed == 1
        assert service.get_request("req-1") is None

    async def test_get_request_returns_none_for_unknown(self, elicitation_service):
        """get_request() - 존재하지 않는 요청 → None"""
        # When: 존재하지 않는 요청 조회
        result = elicitation_service.get_request("nonexistent")

        # Then: None 반환
        assert result is None

    async def test_respond_unknown_request(self, elicitation_service):
        """respond() - 존재하지 않는 요청 → False"""
        # When: 존재하지 않는 요청 응답
        success = await elicitation_service.respond("nonexistent", ElicitationAction.ACCEPT)

        # Then: False 반환
        assert success is False

    async def test_wait_for_response_unknown_request(self, elicitation_service):
        """wait_for_response() - 존재하지 않는 요청 → None"""
        # When: 존재하지 않는 요청 대기
        result = await elicitation_service.wait_for_response("nonexistent", timeout=0.1)

        # Then: None 반환
        assert result is None
