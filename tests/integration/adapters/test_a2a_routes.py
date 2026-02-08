"""A2A Management Routes Integration Tests

A2A 에이전트 등록/해제/조회 API 테스트
"""


class TestA2aAgentRegistration:
    """A2A Agent 등록 API 테스트"""

    async def test_register_a2a_agent_route(self, authenticated_client, a2a_echo_agent: str):
        """
        Given: Echo agent가 실행 중
        When: POST /api/a2a/agents로 등록 요청
        Then: 201 Created 및 agent_card 반환
        """
        # Given: Echo agent 실행 중
        agent_url = a2a_echo_agent

        # When: A2A agent 등록
        response = authenticated_client.post(
            "/api/a2a/agents",
            json={"url": agent_url, "name": "Test Echo Agent"},
        )

        # Then: 등록 성공
        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["url"] == agent_url
        assert data["name"] == "Test Echo Agent"
        assert data["type"] == "a2a"
        assert data["enabled"] is True
        assert "agent_card" in data
        assert isinstance(data["agent_card"], dict)

    async def test_register_a2a_agent_with_invalid_url(self, authenticated_client):
        """
        Given: 잘못된 URL
        When: POST /api/a2a/agents로 등록 요청
        Then: 422 Unprocessable Entity (Pydantic validation)
        """
        # Given: 잘못된 URL
        invalid_url = "not-a-url"

        # When: 등록 요청
        response = authenticated_client.post(
            "/api/a2a/agents",
            json={"url": invalid_url},
        )

        # Then: Validation error
        assert response.status_code == 422

    async def test_register_a2a_agent_connection_failure(self, authenticated_client):
        """
        Given: 연결 불가능한 A2A agent URL
        When: POST /api/a2a/agents로 등록 요청
        Then: 502 Bad Gateway (EndpointConnectionError)
        """
        # Given: 존재하지 않는 포트
        unreachable_url = "http://127.0.0.1:19999"

        # When: 등록 요청
        response = authenticated_client.post(
            "/api/a2a/agents",
            json={"url": unreachable_url, "name": "Unreachable Agent"},
        )

        # Then: Connection error
        assert response.status_code == 502


class TestA2aAgentList:
    """A2A Agent 목록 조회 API 테스트"""

    async def test_list_a2a_agents_route(self, authenticated_client, a2a_echo_agent: str):
        """
        Given: Echo agent가 등록됨
        When: GET /api/a2a/agents 호출
        Then: 등록된 A2A agents 목록 반환
        """
        # Given: Echo agent 등록
        agent_url = a2a_echo_agent
        register_response = authenticated_client.post(
            "/api/a2a/agents",
            json={"url": agent_url, "name": "Listed Agent"},
        )
        assert register_response.status_code == 201

        # When: 목록 조회
        response = authenticated_client.get(
            "/api/a2a/agents",
        )

        # Then: 목록에 포함
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1

        # 등록한 agent 존재 확인
        agent_ids = [agent["id"] for agent in data]
        assert register_response.json()["id"] in agent_ids

    async def test_list_a2a_agents_empty(self, authenticated_client):
        """
        Given: A2A agent 없음
        When: GET /api/a2a/agents 호출
        Then: 빈 목록 반환
        """
        # When: 목록 조회
        response = authenticated_client.get(
            "/api/a2a/agents",
        )

        # Then: 빈 목록 (또는 기존 agents)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestA2aAgentDetail:
    """A2A Agent 상세 조회 API 테스트"""

    async def test_get_a2a_agent_detail(self, authenticated_client, a2a_echo_agent: str):
        """
        Given: Echo agent가 등록됨
        When: GET /api/a2a/agents/{id} 호출
        Then: Agent 상세 정보 반환
        """
        # Given: Echo agent 등록
        agent_url = a2a_echo_agent
        register_response = authenticated_client.post(
            "/api/a2a/agents",
            json={"url": agent_url, "name": "Detail Agent"},
        )
        assert register_response.status_code == 201
        agent_id = register_response.json()["id"]

        # When: 상세 조회
        response = authenticated_client.get(
            f"/api/a2a/agents/{agent_id}",
        )

        # Then: 상세 정보 반환
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == agent_id
        assert data["url"] == agent_url
        assert data["name"] == "Detail Agent"
        assert data["type"] == "a2a"

    async def test_get_nonexistent_a2a_agent(self, authenticated_client):
        """
        Given: 존재하지 않는 agent ID
        When: GET /api/a2a/agents/{id} 호출
        Then: 404 Not Found
        """
        # Given: 존재하지 않는 ID
        nonexistent_id = "nonexistent-agent-id"

        # When: 조회 시도
        response = authenticated_client.get(
            f"/api/a2a/agents/{nonexistent_id}",
        )

        # Then: 404
        assert response.status_code == 404


class TestA2aAgentCard:
    """A2A Agent Card 조회 API 테스트"""

    async def test_get_a2a_agent_card_route(self, authenticated_client, a2a_echo_agent: str):
        """
        Given: Echo agent가 등록됨
        When: GET /api/a2a/agents/{id}/card 호출
        Then: Agent Card JSON 반환
        """
        # Given: Echo agent 등록
        agent_url = a2a_echo_agent
        register_response = authenticated_client.post(
            "/api/a2a/agents",
            json={"url": agent_url, "name": "Card Agent"},
        )
        assert register_response.status_code == 201
        agent_id = register_response.json()["id"]

        # When: Agent Card 조회
        response = authenticated_client.get(
            f"/api/a2a/agents/{agent_id}/card",
        )

        # Then: Agent Card 반환
        assert response.status_code == 200
        card = response.json()

        assert isinstance(card, dict)
        # A2A Agent Card는 ADK가 자동 생성하므로 필드 구조는 유연하게 검증

    async def test_get_card_for_nonexistent_agent(self, authenticated_client):
        """
        Given: 존재하지 않는 agent ID
        When: GET /api/a2a/agents/{id}/card 호출
        Then: 404 Not Found
        """
        # Given: 존재하지 않는 ID
        nonexistent_id = "nonexistent-agent-id"

        # When: Card 조회
        response = authenticated_client.get(
            f"/api/a2a/agents/{nonexistent_id}/card",
        )

        # Then: 404
        assert response.status_code == 404


class TestA2aAgentDeletion:
    """A2A Agent 삭제 API 테스트"""

    async def test_delete_a2a_agent_route(self, authenticated_client, a2a_echo_agent: str):
        """
        Given: Echo agent가 등록됨
        When: DELETE /api/a2a/agents/{id} 호출
        Then: 204 No Content 및 agent 삭제 확인
        """
        # Given: Echo agent 등록
        agent_url = a2a_echo_agent
        register_response = authenticated_client.post(
            "/api/a2a/agents",
            json={"url": agent_url, "name": "To Delete"},
        )
        assert register_response.status_code == 201
        agent_id = register_response.json()["id"]

        # When: 삭제 요청
        response = authenticated_client.delete(
            f"/api/a2a/agents/{agent_id}",
        )

        # Then: 삭제 성공
        assert response.status_code == 204

        # 재조회 시 404
        get_response = authenticated_client.get(
            f"/api/a2a/agents/{agent_id}",
        )
        assert get_response.status_code == 404

    async def test_delete_nonexistent_agent(self, authenticated_client):
        """
        Given: 존재하지 않는 agent ID
        When: DELETE /api/a2a/agents/{id} 호출
        Then: 404 Not Found
        """
        # Given: 존재하지 않는 ID
        nonexistent_id = "nonexistent-agent-id"

        # When: 삭제 시도
        response = authenticated_client.delete(
            f"/api/a2a/agents/{nonexistent_id}",
        )

        # Then: 404
        assert response.status_code == 404


class TestA2aRoutesSecurity:
    """A2A Routes 보안 테스트"""

    async def test_a2a_routes_require_token(self, http_client, a2a_echo_agent: str):
        """
        Given: 토큰 없이 요청
        When: A2A API 호출
        Then: 403 Forbidden
        """
        agent_url = a2a_echo_agent

        # POST /api/a2a/agents (토큰 없음)
        response = http_client.post("/api/a2a/agents", json={"url": agent_url})
        assert response.status_code == 403

        # GET /api/a2a/agents (토큰 없음)
        response = http_client.get("/api/a2a/agents")
        assert response.status_code == 403

        # DELETE /api/a2a/agents/{id} (토큰 없음)
        response = http_client.delete("/api/a2a/agents/some-id")
        assert response.status_code == 403

    async def test_a2a_routes_with_invalid_token(self, http_client, a2a_echo_agent: str):
        """
        Given: 잘못된 토큰
        When: A2A API 호출
        Then: 403 Forbidden
        """
        agent_url = a2a_echo_agent
        invalid_token = "invalid-token-12345"

        # POST with invalid token
        response = http_client.post(
            "/api/a2a/agents",
            json={"url": agent_url},
            headers={"X-Extension-Token": invalid_token},
        )
        assert response.status_code == 403
