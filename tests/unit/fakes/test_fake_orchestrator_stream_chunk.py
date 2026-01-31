"""FakeOrchestrator StreamChunk 지원 테스트 (RED phase)

Step 2.2: FakeOrchestrator가 StreamChunk를 yield하는지 검증합니다.
"""

import pytest

from src.domain.entities.stream_chunk import StreamChunk
from tests.unit.fakes import FakeOrchestrator


class TestFakeOrchestratorStreamChunk:
    """FakeOrchestrator가 StreamChunk를 yield하는지 검증"""

    @pytest.mark.asyncio
    async def test_process_message_yields_stream_chunks(self):
        """process_message가 StreamChunk 객체를 yield해야 함"""
        # Given
        orchestrator = FakeOrchestrator()

        # When
        chunks = []
        async for chunk in orchestrator.process_message("Hello", "conv-1"):
            chunks.append(chunk)

        # Then
        assert len(chunks) == 2
        assert all(isinstance(c, StreamChunk) for c in chunks)
        assert chunks[0].type == "text"
        assert chunks[0].content == "Hello! "
        assert chunks[1].type == "text"
        assert chunks[1].content == "How can I help you?"

    @pytest.mark.asyncio
    async def test_set_responses_accepts_stream_chunks(self):
        """set_responses가 StreamChunk 리스트를 수용해야 함"""
        # Given
        orchestrator = FakeOrchestrator()
        custom_chunks = [
            StreamChunk.text("Custom "),
            StreamChunk.tool_call("search", {"query": "test"}),
            StreamChunk.tool_result("search", "result data"),
            StreamChunk.text("response"),
        ]
        orchestrator.set_responses(custom_chunks)

        # When
        chunks = []
        async for chunk in orchestrator.process_message("Test", "conv-1"):
            chunks.append(chunk)

        # Then
        assert len(chunks) == 4
        assert chunks[0] == StreamChunk.text("Custom ")
        assert chunks[1].type == "tool_call"
        assert chunks[1].tool_name == "search"
        assert chunks[2].type == "tool_result"
        assert chunks[3].type == "text"

    @pytest.mark.asyncio
    async def test_default_responses_are_text_stream_chunks(self):
        """기본 응답이 text 타입 StreamChunk여야 함"""
        # Given
        orchestrator = FakeOrchestrator()

        # Then
        assert all(isinstance(r, StreamChunk) for r in orchestrator.responses)
        assert all(r.type == "text" for r in orchestrator.responses)
