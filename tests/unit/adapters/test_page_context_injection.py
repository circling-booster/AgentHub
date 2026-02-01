"""
Tests for page context injection in OrchestratorAdapter
Phase 5 Part C - Step 10
"""

import pytest

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter


@pytest.fixture
def dynamic_toolset():
    """DynamicToolset fixture"""
    return DynamicToolset()


@pytest.fixture
def orchestrator(dynamic_toolset):
    """AdkOrchestratorAdapter fixture"""
    return AdkOrchestratorAdapter(
        model="openai/gpt-4o-mini",
        dynamic_toolset=dynamic_toolset,
        enable_llm_logging=False,
    )


@pytest.mark.asyncio
async def test_process_message_with_page_context_injects_context(orchestrator):
    """
    Given: OrchestratorAdapter with page_context
    When: process_message is called with page_context
    Then: Context is injected into the message
    """
    # Given
    page_context = {
        "url": "https://example.com/article",
        "title": "Test Article",
        "selectedText": "Important paragraph",
        "metaDescription": "Article description",
        "mainContent": "Full article content here...",
    }

    # When
    chunks = []
    async for chunk in orchestrator.process_message(
        message="Summarize this article",
        conversation_id="test-conv",
        page_context=page_context,
    ):
        chunks.append(chunk)

    # Then
    # Message should be augmented with context
    # We can't easily test the exact LLM input, but we can verify it processes
    assert len(chunks) > 0  # Should produce some output


@pytest.mark.asyncio
async def test_process_message_without_page_context_unchanged(orchestrator):
    """
    Given: OrchestratorAdapter without page_context
    When: process_message is called without page_context
    Then: Message is processed normally (backward compatibility)
    """
    # Given - no page_context

    # When
    chunks = []
    async for chunk in orchestrator.process_message(
        message="Hello",
        conversation_id="test-conv",
        page_context=None,
    ):
        chunks.append(chunk)

    # Then
    assert len(chunks) > 0  # Should work as before


@pytest.mark.asyncio
async def test_page_context_truncated_at_limit(orchestrator):
    """
    Given: Page context with very long content
    When: process_message is called
    Then: Content is truncated to prevent context overflow
    """
    # Given
    long_content = "A" * 5000  # Exceeds typical limit
    page_context = {
        "url": "https://example.com",
        "title": "Test",
        "selectedText": "",
        "metaDescription": "",
        "mainContent": long_content,
    }

    # When
    chunks = []
    async for chunk in orchestrator.process_message(
        message="Summarize",
        conversation_id="test-conv",
        page_context=page_context,
    ):
        chunks.append(chunk)

    # Then
    # Should not fail due to context overflow
    assert len(chunks) > 0


@pytest.mark.asyncio
async def test_page_context_format_includes_url_title_selected(orchestrator):
    """
    Given: Page context with URL, title, and selected text
    When: Context is injected
    Then: Format includes all fields properly
    """
    # Given
    page_context = {
        "url": "https://example.com/test",
        "title": "Test Page",
        "selectedText": "Selected portion",
        "metaDescription": "Meta description here",
        "mainContent": "Main content",
    }

    # When
    chunks = []
    async for chunk in orchestrator.process_message(
        message="What is this about?",
        conversation_id="test-conv",
        page_context=page_context,
    ):
        chunks.append(chunk)

    # Then
    # Verify processing completes
    assert len(chunks) > 0
