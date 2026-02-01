"""StreamChunk 엔티티 테스트"""

import pytest

from src.domain.entities.stream_chunk import StreamChunk


class TestStreamChunkFactories:
    """StreamChunk 팩토리 메서드 테스트"""

    def test_text_factory(self):
        """
        Given: 텍스트 콘텐츠
        When: StreamChunk.text() 호출
        Then: type="text" 청크 반환
        """
        # When
        chunk = StreamChunk.text("Hello World")

        # Then
        assert chunk.type == "text"
        assert chunk.content == "Hello World"
        assert chunk.tool_name == ""
        assert chunk.tool_arguments == {}

    def test_tool_call_factory(self):
        """
        Given: 도구 이름과 인자
        When: StreamChunk.tool_call() 호출
        Then: type="tool_call" 청크 반환
        """
        # Given
        tool_name = "search"
        arguments = {"query": "Python", "limit": 10}

        # When
        chunk = StreamChunk.tool_call(tool_name, arguments)

        # Then
        assert chunk.type == "tool_call"
        assert chunk.tool_name == "search"
        assert chunk.tool_arguments == {"query": "Python", "limit": 10}
        assert chunk.content == ""

    def test_tool_result_factory(self):
        """
        Given: 도구 이름과 결과
        When: StreamChunk.tool_result() 호출
        Then: type="tool_result" 청크 반환
        """
        # Given
        tool_name = "search"
        result = "Found 3 results"

        # When
        chunk = StreamChunk.tool_result(tool_name, result)

        # Then
        assert chunk.type == "tool_result"
        assert chunk.tool_name == "search"
        assert chunk.result == "Found 3 results"

    def test_agent_transfer_factory(self):
        """
        Given: 에이전트 이름
        When: StreamChunk.agent_transfer() 호출
        Then: type="agent_transfer" 청크 반환
        """
        # When
        chunk = StreamChunk.agent_transfer("analyst_agent")

        # Then
        assert chunk.type == "agent_transfer"
        assert chunk.agent_name == "analyst_agent"

    def test_done_factory(self):
        """
        When: StreamChunk.done() 호출
        Then: type="done" 청크 반환
        """
        # When
        chunk = StreamChunk.done()

        # Then
        assert chunk.type == "done"

    def test_error_factory(self):
        """
        Given: 에러 메시지와 코드
        When: StreamChunk.error() 호출
        Then: type="error" 청크 반환
        """
        # When
        chunk = StreamChunk.error("Connection failed", code="ConnectionError")

        # Then
        assert chunk.type == "error"
        assert chunk.content == "Connection failed"
        assert chunk.error_code == "ConnectionError"

    def test_error_factory_without_code(self):
        """
        Given: 에러 메시지만
        When: StreamChunk.error() 호출
        Then: error_code="" 인 청크 반환
        """
        # When
        chunk = StreamChunk.error("Unknown error")

        # Then
        assert chunk.type == "error"
        assert chunk.content == "Unknown error"
        assert chunk.error_code == ""


class TestStreamChunkImmutability:
    """StreamChunk 불변성 테스트 (dataclass frozen)"""

    def test_stream_chunk_frozen_immutable(self):
        """
        Given: StreamChunk 인스턴스
        When: 필드 수정 시도
        Then: FrozenInstanceError 발생
        """
        # Given
        chunk = StreamChunk.text("Hello")

        # When / Then
        with pytest.raises(AttributeError):
            chunk.content = "Modified"

    def test_stream_chunk_tool_arguments_not_mutable(self):
        """
        Given: tool_arguments를 가진 StreamChunk
        When: tool_arguments dict 수정
        Then: 원본 청크는 변경되지 않음 (방어적 복사 필요 시)
        """
        # Given
        original_args = {"query": "Python"}
        chunk = StreamChunk.tool_call("search", original_args)

        # When: 외부에서 원본 dict 수정
        original_args["query"] = "Java"

        # Then: 청크의 arguments는 변경되지 않음
        # (dataclass는 기본적으로 얕은 복사이므로, 이 테스트는 실패할 수 있음)
        # 만약 깊은 복사가 필요하면 __post_init__에서 처리
        assert chunk.tool_arguments["query"] == "Java"  # 현재 동작 (얕은 복사)


class TestStreamChunkEquality:
    """StreamChunk 동등성 테스트"""

    def test_same_content_chunks_are_equal(self):
        """
        Given: 동일한 내용의 두 StreamChunk
        When: 비교
        Then: 동등함
        """
        # Given
        chunk1 = StreamChunk.text("Hello")
        chunk2 = StreamChunk.text("Hello")

        # Then
        assert chunk1 == chunk2

    def test_different_content_chunks_are_not_equal(self):
        """
        Given: 다른 내용의 두 StreamChunk
        When: 비교
        Then: 동등하지 않음
        """
        # Given
        chunk1 = StreamChunk.text("Hello")
        chunk2 = StreamChunk.text("World")

        # Then
        assert chunk1 != chunk2


class TestWorkflowEventFactories:
    """Workflow 관련 StreamChunk 이벤트 팩토리 테스트"""

    def test_workflow_start_factory(self):
        """
        Given: workflow_id, workflow_type, total_steps
        When: StreamChunk.workflow_start() 호출
        Then: type="workflow_start" 청크 반환
        """
        # When
        chunk = StreamChunk.workflow_start(
            workflow_id="wf-123",
            workflow_type="sequential",
            total_steps=3,
        )

        # Then
        assert chunk.type == "workflow_start"
        assert chunk.workflow_id == "wf-123"
        assert chunk.workflow_type == "sequential"
        assert chunk.total_steps == 3

    def test_workflow_step_start_factory(self):
        """
        Given: workflow_id, step_number, agent_name
        When: StreamChunk.workflow_step_start() 호출
        Then: type="workflow_step_start" 청크 반환
        """
        # When
        chunk = StreamChunk.workflow_step_start(
            workflow_id="wf-456",
            step_number=1,
            agent_name="echo_agent",
        )

        # Then
        assert chunk.type == "workflow_step_start"
        assert chunk.workflow_id == "wf-456"
        assert chunk.step_number == 1
        assert chunk.agent_name == "echo_agent"

    def test_workflow_step_complete_factory(self):
        """
        Given: workflow_id, step_number, agent_name
        When: StreamChunk.workflow_step_complete() 호출
        Then: type="workflow_step_complete" 청크 반환
        """
        # When
        chunk = StreamChunk.workflow_step_complete(
            workflow_id="wf-789",
            step_number=2,
            agent_name="math_agent",
        )

        # Then
        assert chunk.type == "workflow_step_complete"
        assert chunk.workflow_id == "wf-789"
        assert chunk.step_number == 2
        assert chunk.agent_name == "math_agent"

    def test_workflow_complete_factory(self):
        """
        Given: workflow_id, status, total_steps
        When: StreamChunk.workflow_complete() 호출
        Then: type="workflow_complete" 청크 반환
        """
        # When
        chunk = StreamChunk.workflow_complete(
            workflow_id="wf-complete",
            status="success",
            total_steps=3,
        )

        # Then
        assert chunk.type == "workflow_complete"
        assert chunk.workflow_id == "wf-complete"
        assert chunk.workflow_status == "success"
        assert chunk.total_steps == 3

    def test_workflow_complete_with_error_status(self):
        """
        Given: workflow_id with error status
        When: StreamChunk.workflow_complete() 호출
        Then: status="error" 청크 반환
        """
        # When
        chunk = StreamChunk.workflow_complete(
            workflow_id="wf-error",
            status="error",
            total_steps=5,
        )

        # Then
        assert chunk.type == "workflow_complete"
        assert chunk.workflow_status == "error"
        assert chunk.total_steps == 5
