"""
Tests for page_context in Chat API
Phase 5 Part C - Step 10
"""

from tests.integration.conftest import TEST_EXTENSION_TOKEN


def test_chat_request_accepts_page_context(http_client):
    """
    Given: ChatRequest schema
    When: POST /api/chat/stream with page_context field
    Then: Request is accepted (schema validation passes)
    """
    # Given
    request_data = {
        "conversation_id": None,
        "message": "Summarize this page",
        "page_context": {
            "url": "https://example.com",
            "title": "Example Page",
            "selectedText": "Some selected text",
            "metaDescription": "A description",
            "mainContent": "Main page content here",
        },
    }

    # When
    response = http_client.post(
        "/api/chat/stream",
        json=request_data,
        headers={"X-Extension-Token": TEST_EXTENSION_TOKEN},
    )

    # Then
    # Schema validation should pass (status 200 or streaming started)
    # Note: Actual streaming test is done elsewhere
    assert response.status_code in [200, 204]  # Accept if streaming starts


def test_chat_request_accepts_null_page_context(http_client):
    """
    Given: ChatRequest schema
    When: POST with page_context = None
    Then: Request is accepted
    """
    # Given
    request_data = {
        "conversation_id": None,
        "message": "Hello",
        "page_context": None,
    }

    # When
    response = http_client.post(
        "/api/chat/stream",
        json=request_data,
        headers={"X-Extension-Token": TEST_EXTENSION_TOKEN},
    )

    # Then
    assert response.status_code in [200, 204]


def test_chat_request_accepts_missing_page_context(http_client):
    """
    Given: ChatRequest schema
    When: POST without page_context field (backward compatibility)
    Then: Request is accepted
    """
    # Given
    request_data = {
        "conversation_id": None,
        "message": "Hello",
    }

    # When
    response = http_client.post(
        "/api/chat/stream",
        json=request_data,
        headers={"X-Extension-Token": TEST_EXTENSION_TOKEN},
    )

    # Then
    assert response.status_code in [200, 204]
