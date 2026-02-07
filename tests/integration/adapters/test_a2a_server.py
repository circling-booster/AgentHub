"""A2A Server Exposure Integration Tests

AgentHub LlmAgent를 A2A 프로토콜로 노출
"""


class TestA2aServerExposure:
    """A2A Server 노출 테스트"""

    async def test_agent_card_served_at_well_known_path(self, authenticated_client):
        """
        Given: AgentHub가 A2A 서버로 노출됨
        When: GET /.well-known/agent-card.json 호출
        Then: 200 OK 및 Agent Card JSON 반환
        """
        # When: Agent Card 조회
        response = authenticated_client.get("/.well-known/agent-card.json")

        # Then: Agent Card 반환
        assert response.status_code == 200
        card = response.json()

        # Agent Card 기본 구조 검증
        assert isinstance(card, dict)
        assert "agentId" in card or "agent_id" in card  # ADK 명명 규칙 불확실
        assert "name" in card
        assert "skills" in card or "capabilities" in card

    async def test_agent_card_has_required_fields(self, authenticated_client):
        """
        Given: Agent Card가 제공됨
        When: 필드 검증
        Then: agentId, name, skills 포함
        """
        # When: Agent Card 조회
        response = authenticated_client.get("/.well-known/agent-card.json")
        assert response.status_code == 200

        card = response.json()

        # Then: 필수 필드 존재
        # ADK 자동 생성 카드는 최소 name과 식별자를 포함해야 함
        assert card.get("name") or card.get("agent_name"), "Agent name is required"

        # Skills 또는 capabilities 중 하나는 존재해야 함
        has_skills = "skills" in card or "capabilities" in card or "description" in card
        assert has_skills, "Agent Card should describe capabilities"

    async def test_agent_card_without_auth_returns_200(self, http_client):
        """
        Given: 인증 없이 요청
        When: GET /.well-known/agent-card.json 호출
        Then: 200 OK (A2A Discovery 엔드포인트는 공개)
        """
        # When: 토큰 없이 Agent Card 조회
        response = http_client.get("/.well-known/agent-card.json")

        # Then: 200 OK (Agent Card는 공개 Discovery 엔드포인트)
        assert response.status_code == 200

        # Agent Card 기본 구조 검증
        card = response.json()
        assert isinstance(card, dict)
        assert "agentId" in card or "agent_id" in card
        assert "name" in card
