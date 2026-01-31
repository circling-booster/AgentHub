"""OrchestratorAdapter Logging Tests (TDD RED - Step 7)

Phase 4 Part B: Structured Logging for OrchestratorAdapter
"""

import logging
from unittest.mock import AsyncMock

import pytest

from src.adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter


@pytest.mark.asyncio
async def test_rebuild_agent_logs_tool_and_agent_counts(caplog):
    """_rebuild_agent()가 MCP 도구와 A2A 에이전트 개수를 로깅해야 함"""
    # Given: OrchestratorAdapter with mocked DynamicToolset
    from unittest.mock import MagicMock

    mock_toolset = AsyncMock()
    mock_toolset.get_tools = AsyncMock(return_value=[])
    mock_toolset.get_registered_info = MagicMock(  # 일반 함수이므로 MagicMock 사용
        return_value={
            "endpoint-1": {
                "name": "MCP Server 1",
                "url": "http://localhost:9000/mcp",
                "tools": ["tool_a", "tool_b"],
            },
            "endpoint-2": {
                "name": "MCP Server 2",
                "url": "http://localhost:9001/mcp",
                "tools": ["tool_c", "tool_d", "tool_e"],
            },
        }
    )

    adapter = AdkOrchestratorAdapter(
        model="openai/gpt-4o-mini", dynamic_toolset=mock_toolset, enable_llm_logging=False
    )

    await adapter.initialize()
    caplog.clear()

    # When: _rebuild_agent() 호출
    with caplog.at_level(logging.INFO):
        await adapter._rebuild_agent()

    # Then: MCP 도구/에이전트 개수 로깅
    info_logs = [r for r in caplog.records if r.levelname == "INFO"]
    assert len(info_logs) > 0

    # extra 필드 확인
    log_with_extra = [r for r in info_logs if hasattr(r, "total_mcp_tools")]
    assert len(log_with_extra) > 0
    assert log_with_extra[0].total_mcp_tools == 5  # tool_a, tool_b, tool_c, tool_d, tool_e
    assert log_with_extra[0].mcp_endpoints == 2
    assert log_with_extra[0].a2a_agents == 0


@pytest.mark.asyncio
async def test_initialize_logs_model_name(caplog):
    """initialize()가 모델 이름을 로깅해야 함 (회귀 방지)"""
    # Given: OrchestratorAdapter
    from unittest.mock import MagicMock

    mock_toolset = AsyncMock()
    mock_toolset.get_tools = AsyncMock(return_value=[])
    mock_toolset.get_registered_info = MagicMock(return_value={})

    adapter = AdkOrchestratorAdapter(
        model="openai/gpt-4o-mini", dynamic_toolset=mock_toolset, enable_llm_logging=False
    )

    # When: initialize() 호출
    with caplog.at_level(logging.INFO):
        await adapter.initialize()

    # Then: 모델 이름 로깅
    info_logs = [r for r in caplog.records if r.levelname == "INFO"]
    assert len(info_logs) > 0
    assert any("gpt-4o-mini" in record.message for record in info_logs)
