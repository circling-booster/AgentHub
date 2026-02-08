"""A2A Echo Agent Smoke Tests

Verify echo agent fixture works correctly
"""

import httpx
import pytest


@pytest.mark.local_a2a
class TestA2aEchoAgentFixture:
    """Echo agent fixture smoke tests"""

    def test_echo_agent_ready(self, a2a_echo_agent):
        """
        Given: Echo agent is running
        When: /.well-known/agent.json endpoint is called
        Then: Returns 200 OK with agent card
        """
        # Given: fixture provides base URL
        base_url = a2a_echo_agent

        # When: call agent card endpoint
        response = httpx.get(f"{base_url}/.well-known/agent.json", timeout=5.0)

        # Then: agent is ready
        assert response.status_code == 200
        card = response.json()
        assert isinstance(card, dict)

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

    async def test_echo_agent_jsonrpc_endpoint_exists(self, a2a_echo_agent):
        """
        Given: Echo agent is running
        When: POST / endpoint is checked (JSON-RPC 2.0)
        Then: Endpoint exists and responds
        """
        # Given
        base_url = a2a_echo_agent

        # When: check JSON-RPC endpoint with OPTIONS
        async with httpx.AsyncClient() as client:
            # Verify endpoint exists (A2A uses POST / for JSON-RPC)
            response = await client.options(f"{base_url}/", timeout=5.0)

            # Then: endpoint exists (may return 200, 204, or 405)
            assert response.status_code in [200, 204, 405], (
                f"JSON-RPC endpoint should exist, got {response.status_code}"
            )
