"""Zombie Task Cancellation Tests

SSE 스트리밍 중 클라이언트 연결 해제 시 태스크 정리 검증
"""

import asyncio
import logging

import pytest

from src.domain.entities.stream_chunk import StreamChunk

# Caplog 테스트를 위해 로거 가져오기
logger = logging.getLogger("src.adapters.inbound.http.routes.chat")


class TestZombieTaskCancellation:
    """Zombie Task 취소 테스트"""

    async def test_cancelled_error_propagates_and_logged(self, caplog):
        """
        Given: SSE 생성기 실행 중
        When: asyncio.CancelledError 발생 시
        Then: 에러가 전파되고 'Stream cancelled' 로그 기록됨
        """
        from unittest.mock import AsyncMock, MagicMock

        from src.adapters.inbound.http.routes.chat import chat_stream
        from src.adapters.inbound.http.schemas.chat import ChatRequest

        # Given: Mock request, orchestrator
        request = MagicMock()
        request.is_disconnected = AsyncMock(return_value=False)

        body = ChatRequest(conversation_id="test-conv", message="test")

        orchestrator = MagicMock()

        # orchestrator.send_message가 async generator로 CancelledError를 발생시킴
        async def send_message_gen(*args, **kwargs):
            yield StreamChunk.text("chunk1")
            await asyncio.sleep(0.01)
            # CancelledError 발생
            raise asyncio.CancelledError()

        orchestrator.send_message = send_message_gen

        # When: chat_stream 호출 (DI 없이 직접 호출)
        with caplog.at_level(logging.INFO, logger="src.adapters.inbound.http.routes.chat"):
            response = await chat_stream.__wrapped__(request, body, orchestrator)

            # Then: StreamingResponse 반환됨
            assert response is not None

            # 생성기 실행 시 CancelledError 전파 확인
            with pytest.raises(asyncio.CancelledError):
                async for _ in response.body_iterator:
                    pass

        # 로그 확인
        assert any("Stream cancelled" in record.message for record in caplog.records)

    async def test_disconnect_detection_stops_stream(self, caplog):
        """
        Given: SSE 스트리밍 진행 중
        When: request.is_disconnected()가 True를 반환하면
        Then: 스트림이 중단되고 'Client disconnected' 로그 기록됨
        """
        from unittest.mock import MagicMock

        from src.adapters.inbound.http.routes.chat import chat_stream
        from src.adapters.inbound.http.schemas.chat import ChatRequest

        # Given
        request = MagicMock()
        disconnect_count = 0

        async def mock_is_disconnected():
            nonlocal disconnect_count
            disconnect_count += 1
            # 두 번째 호출부터 연결 해제
            return disconnect_count > 1

        request.is_disconnected = mock_is_disconnected

        body = ChatRequest(conversation_id="test-conv-2", message="Hello")

        orchestrator = MagicMock()

        # 여러 chunk를 반환하는 제너레이터
        async def send_message_gen(*args, **kwargs):
            for i in range(10):
                await asyncio.sleep(0.01)
                yield StreamChunk.text(f"chunk_{i}")

        orchestrator.send_message = send_message_gen

        # When
        with caplog.at_level(logging.INFO, logger="src.adapters.inbound.http.routes.chat"):
            response = await chat_stream.__wrapped__(request, body, orchestrator)

            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)

        # Then: 스트림이 중단됨 (10개 미만)
        assert len(chunks) < 10, f"Expected stream to stop early, got {len(chunks)} chunks"

        # 로그 확인
        assert any("Client disconnected" in record.message for record in caplog.records)
