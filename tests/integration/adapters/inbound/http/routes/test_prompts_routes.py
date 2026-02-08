"""Prompts API Routes Integration Tests

SDK Track: MCP Prompts 관리 (list, get)
"""

import pytest


@pytest.mark.local_mcp
class TestPromptsRoutes:
    """Prompts API 통합 테스트 (MCP Synapse 필요)"""

    async def test_list_prompts_returns_list(self, authenticated_client, mcp_synapse_endpoint):
        """프롬프트 목록 조회 성공

        Given: MCP 서버 등록됨
        When: GET /api/mcp/servers/{endpoint_id}/prompts
        Then: 200 OK, prompts 목록 반환
        """
        response = authenticated_client.get(
            f"/api/mcp/servers/{mcp_synapse_endpoint['id']}/prompts"
        )

        assert response.status_code == 200
        data = response.json()
        assert "prompts" in data
        assert isinstance(data["prompts"], list)
        assert len(data["prompts"]) > 0

        # 첫 번째 프롬프트 구조 확인
        first_prompt = data["prompts"][0]
        assert "name" in first_prompt
        assert "description" in first_prompt
        assert "arguments" in first_prompt

    async def test_list_prompts_endpoint_not_found(self, authenticated_client):
        """존재하지 않는 엔드포인트 → 404

        Given: 존재하지 않는 endpoint_id
        When: GET /api/mcp/servers/nonexistent/prompts
        Then: 404 Not Found
        """
        response = authenticated_client.get("/api/mcp/servers/nonexistent/prompts")

        assert response.status_code == 404
        assert "error" in response.json() or "detail" in response.json()

    async def test_get_prompt_with_arguments_returns_content(
        self, authenticated_client, mcp_synapse_endpoint
    ):
        """프롬프트 렌더링 (arguments 포함) 성공

        Given: MCP 서버 등록됨 + 프롬프트 존재
        When: POST /api/mcp/servers/{endpoint_id}/prompts/{name} with arguments
        Then: 200 OK, 렌더링된 content 반환
        """
        # 먼저 목록 조회하여 실제 프롬프트 이름 가져오기
        list_response = authenticated_client.get(
            f"/api/mcp/servers/{mcp_synapse_endpoint['id']}/prompts"
        )
        prompts = list_response.json()["prompts"]
        assert len(prompts) > 0
        test_prompt = prompts[0]

        # required arguments 준비
        required_args = {
            arg["name"]: "test_value" for arg in test_prompt["arguments"] if arg["required"]
        }

        # 프롬프트 렌더링
        response = authenticated_client.post(
            f"/api/mcp/servers/{mcp_synapse_endpoint['id']}/prompts/{test_prompt['name']}",
            json={"arguments": required_args},  # required arguments 제공
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert isinstance(data["content"], str)
        assert len(data["content"]) > 0

    async def test_get_prompt_with_required_arguments(
        self, authenticated_client, mcp_synapse_endpoint
    ):
        """필수 arguments가 있는 프롬프트 렌더링

        Given: required arguments가 있는 프롬프트
        When: POST with valid arguments
        Then: 200 OK, 렌더링된 content 반환
        """
        # 먼저 목록 조회
        list_response = authenticated_client.get(
            f"/api/mcp/servers/{mcp_synapse_endpoint['id']}/prompts"
        )
        prompts = list_response.json()["prompts"]

        # required arguments가 있는 프롬프트 찾기
        prompt_with_args = None
        for p in prompts:
            if p["arguments"] and any(arg["required"] for arg in p["arguments"]):
                prompt_with_args = p
                break

        if prompt_with_args is None:
            pytest.skip("No prompt with required arguments found")

        # arguments 준비
        required_args = {
            arg["name"]: "test_value" for arg in prompt_with_args["arguments"] if arg["required"]
        }

        # 프롬프트 렌더링
        response = authenticated_client.post(
            f"/api/mcp/servers/{mcp_synapse_endpoint['id']}/prompts/{prompt_with_args['name']}",
            json={"arguments": required_args},
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "test_value" in data["content"]  # arguments가 렌더링됨

    async def test_get_prompt_not_found(self, authenticated_client, mcp_synapse_endpoint):
        """존재하지 않는 프롬프트 → 404

        Given: MCP 서버 등록됨
        When: POST /api/mcp/servers/{endpoint_id}/prompts/nonexistent
        Then: 404 Not Found
        """
        response = authenticated_client.post(
            f"/api/mcp/servers/{mcp_synapse_endpoint['id']}/prompts/nonexistent_prompt",
            json={"arguments": {}},
        )

        assert response.status_code == 404
        assert "error" in response.json() or "detail" in response.json()

    async def test_get_prompt_endpoint_not_found(self, authenticated_client):
        """존재하지 않는 엔드포인트 → 404

        Given: 존재하지 않는 endpoint_id
        When: POST /api/mcp/servers/nonexistent/prompts/{name}
        Then: 404 Not Found
        """
        response = authenticated_client.post(
            "/api/mcp/servers/nonexistent/prompts/test_prompt",
            json={"arguments": {}},
        )

        assert response.status_code == 404
        assert "error" in response.json() or "detail" in response.json()
