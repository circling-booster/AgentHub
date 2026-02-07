"""DynamicToolset call_tool() 재시도 로직 테스트

TDD Phase: RED - 재시도 테스트 작성
"""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.config.settings import McpSettings, Settings


@pytest.fixture
def settings_with_retry():
    """재시도 설정이 있는 Settings"""
    settings = Settings()
    settings.mcp = McpSettings(
        max_active_tools=30,
        cache_ttl_seconds=300,
        max_retries=2,
        retry_backoff_seconds=0.1,  # 테스트용 짧은 대기시간
    )
    return settings


@pytest.fixture
def dynamic_toolset_with_retry(settings_with_retry):
    """재시도 설정이 있는 DynamicToolset"""
    toolset = DynamicToolset(cache_ttl_seconds=300)
    toolset._settings = settings_with_retry
    return toolset


@pytest.fixture
def mock_toolset_with_failing_tool():
    """실패하는 도구가 있는 Mock MCPToolset"""
    mock_tool = MagicMock()
    mock_tool.name = "failing_tool"
    mock_tool.description = "A tool that fails"

    # 도구 실행이 실패하도록 설정
    async def failing_run(*args, **kwargs):
        raise ConnectionError("Temporary connection error")

    mock_tool.run_async = AsyncMock(side_effect=failing_run)

    mock_toolset = AsyncMock()
    mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])
    mock_toolset.close = AsyncMock()

    return mock_toolset, mock_tool


class TestToolRetryOnTransientError:
    """일시적 에러 시 재시도 테스트"""

    async def test_tool_retries_on_transient_error(
        self, dynamic_toolset_with_retry, mock_toolset_with_failing_tool
    ):
        """
        Given: 일시적 네트워크 에러가 발생하는 도구
        When: call_tool() 호출
        Then: 최대 재시도 횟수만큼 재시도 후 실패
        """
        mock_toolset, mock_tool = mock_toolset_with_failing_tool

        # Mock MCPToolset 등록
        dynamic_toolset_with_retry._mcp_toolsets["test-endpoint"] = mock_toolset

        # 재시도 카운터
        call_count = 0

        async def count_failures(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Temporary connection error")

        mock_tool.run_async = AsyncMock(side_effect=count_failures)

        # When: call_tool 호출
        with pytest.raises(ConnectionError):
            await dynamic_toolset_with_retry.call_tool("failing_tool", {})

        # Then: max_retries + 1회 호출 (첫 시도 + 재시도 2회 = 3회)
        assert call_count == 3

    async def test_tool_succeeds_after_retry(
        self, dynamic_toolset_with_retry, mock_toolset_with_failing_tool
    ):
        """
        Given: 첫 번째 시도에서 실패하고 두 번째에서 성공하는 도구
        When: call_tool() 호출
        Then: 재시도 후 성공
        """
        mock_toolset, mock_tool = mock_toolset_with_failing_tool

        # Mock MCPToolset 등록
        dynamic_toolset_with_retry._mcp_toolsets["test-endpoint"] = mock_toolset

        # 첫 시도 실패, 두 번째 성공
        call_count = 0

        async def fail_then_succeed(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Temporary error")
            return "success"

        mock_tool.run_async = AsyncMock(side_effect=fail_then_succeed)

        # When: call_tool 호출
        result = await dynamic_toolset_with_retry.call_tool("failing_tool", {})

        # Then: 성공 (2회 호출)
        assert result == "success"
        assert call_count == 2


class TestToolNoRetryOnPermanentError:
    """영구 에러 시 재시도 안함 테스트"""

    async def test_tool_no_retry_on_permanent_error(self, dynamic_toolset_with_retry):
        """
        Given: 영구 에러가 발생하는 도구 (ValueError, RuntimeError 등)
        When: call_tool() 호출
        Then: 재시도 없이 즉시 실패
        """
        mock_tool = MagicMock()
        mock_tool.name = "permanent_error_tool"

        call_count = 0

        async def permanent_error(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input - permanent error")

        mock_tool.run_async = AsyncMock(side_effect=permanent_error)

        mock_toolset = AsyncMock()
        mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])

        dynamic_toolset_with_retry._mcp_toolsets["test-endpoint"] = mock_toolset

        # When: call_tool 호출
        with pytest.raises(ValueError):
            await dynamic_toolset_with_retry.call_tool("permanent_error_tool", {})

        # Then: 1회만 호출 (재시도 없음)
        assert call_count == 1


class TestExponentialBackoff:
    """Exponential Backoff 테스트"""

    async def test_exponential_backoff_timing(
        self, dynamic_toolset_with_retry, mock_toolset_with_failing_tool
    ):
        """
        Given: 재시도 backoff가 0.1초로 설정됨
        When: 도구가 계속 실패
        Then: 재시도 간격이 0.1s, 0.2s, 0.4s로 증가
        """
        mock_toolset, mock_tool = mock_toolset_with_failing_tool
        dynamic_toolset_with_retry._mcp_toolsets["test-endpoint"] = mock_toolset

        retry_times = []

        async def track_retry_time(*args, **kwargs):
            retry_times.append(time.time())
            raise ConnectionError("Temporary error")

        mock_tool.run_async = AsyncMock(side_effect=track_retry_time)

        # When: call_tool 호출
        with pytest.raises(ConnectionError):
            await dynamic_toolset_with_retry.call_tool("failing_tool", {})

        # Then: 3회 호출 (첫 시도 + 재시도 2회)
        assert len(retry_times) == 3

        # 첫 재시도: ~0.1초 후
        first_retry_delay = retry_times[1] - retry_times[0]
        assert 0.08 < first_retry_delay < 0.15

        # 두 번째 재시도: ~0.2초 후
        second_retry_delay = retry_times[2] - retry_times[1]
        assert 0.18 < second_retry_delay < 0.25


class TestMaxRetriesExceeded:
    """최대 재시도 초과 테스트"""

    async def test_max_retries_exceeded_raises(
        self, dynamic_toolset_with_retry, mock_toolset_with_failing_tool
    ):
        """
        Given: max_retries = 2
        When: 도구가 3회 이상 실패
        Then: 최종적으로 에러 발생
        """
        mock_toolset, mock_tool = mock_toolset_with_failing_tool
        dynamic_toolset_with_retry._mcp_toolsets["test-endpoint"] = mock_toolset

        # When & Then: max_retries 초과 시 에러 발생
        with pytest.raises(ConnectionError, match="Temporary connection error"):
            await dynamic_toolset_with_retry.call_tool("failing_tool", {})


class TestRetryDisabled:
    """재시도 비활성화 테스트"""

    async def test_retry_disabled_when_max_retries_zero(self):
        """
        Given: max_retries = 0
        When: 도구가 실패
        Then: 재시도 없이 즉시 실패
        """
        # Given: max_retries = 0 설정
        settings = Settings()
        settings.mcp = McpSettings(
            max_active_tools=30,
            cache_ttl_seconds=300,
            max_retries=0,  # 재시도 비활성화
            retry_backoff_seconds=1.0,
        )

        toolset = DynamicToolset(cache_ttl_seconds=300)
        toolset._settings = settings

        # Mock tool 설정
        call_count = 0

        async def fail_immediately(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Error")

        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.run_async = AsyncMock(side_effect=fail_immediately)

        mock_toolset = AsyncMock()
        mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])

        toolset._mcp_toolsets["test-endpoint"] = mock_toolset

        # When: call_tool 호출
        with pytest.raises(ConnectionError):
            await toolset.call_tool("test_tool", {})

        # Then: 1회만 호출 (재시도 없음)
        assert call_count == 1
