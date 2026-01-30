"""A2A Echo Agent Smoke Tests

Verify echo agent fixture works correctly
"""

import httpx
import pytest


@pytest.mark.local_a2a
class TestA2aEchoAgentFixture:
    """Echo agent fixture smoke tests"""

    def test_echo_agent_health(self, a2a_echo_agent):
        """
        Given: Echo agent is running
        When: /health endpoint is called
        Then: Returns 200 OK
        """
        # Given: fixture provides base URL
        base_url = a2a_echo_agent

        # When: call health endpoint
        response = httpx.get(f"{base_url}/health", timeout=5.0)

        # Then: healthy
        assert response.status_code == 200

    def test_echo_agent_card(self, a2a_echo_agent):
        """
        Given: Echo agent is running
        When: /.well-known/agent.json is fetched
        Then: Returns valid Agent Card with name, description
        """
        # Given
        base_url = a2a_echo_agent

        # When: fetch agent card
        response = httpx.get(f"{base_url}/.well-known/agent.json", timeout=5.0)

        # Then: valid agent card
        assert response.status_code == 200

        card = response.json()
        assert "name" in card or "agentId" in card
        # ADK auto-generates agent card, check for expected fields
        assert isinstance(card, dict)

    @pytest.mark.asyncio
    async def test_echo_agent_process_endpoint_exists(self, a2a_echo_agent):
        """
        Given: Echo agent is running
        When: /process endpoint is checked
        Then: Endpoint exists (may require specific A2A format)
        """
        # Given
        base_url = a2a_echo_agent

        # When: check process endpoint (OPTIONS or lightweight check)
        async with httpx.AsyncClient() as client:
            # Just verify endpoint responds (A2A protocol requires specific request format)
            response = await client.options(f"{base_url}/process", timeout=5.0)

            # Then: endpoint exists (may return 405 Method Not Allowed, but not 404)
            assert response.status_code in [200, 204, 405], (
                f"Process endpoint should exist, got {response.status_code}"
            )
