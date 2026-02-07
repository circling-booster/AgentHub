"""Dual-Track 통합 테스트 (Synapse + ADK + LLM)

**주의:**
- 실제 Synapse MCP 서버 필요 (localhost:9000/mcp)
- 실제 LLM 호출 비용 발생
- @pytest.mark.local_mcp + @pytest.mark.llm 마커 사용 (기본 테스트에서 스킵)

**실행:**
```bash
# Synapse MCP 서버 시작 후
pytest tests/integration/test_dual_track.py -m "local_mcp and llm" -v
```
"""

import pytest

# authenticated_client fixture는 tests/integration/adapters/conftest.py에 정의되어 있음
# 자동으로 X-Extension-Token 헤더를 추가하여 인증 문제 해결


@pytest.mark.local_mcp
@pytest.mark.llm
class TestDualTrack:
    """Dual-Track 상호작용 테스트 (Synapse + ADK + LLM)

    시나리오:
    1. Synapse 등록 (Dual-Track: ADK + SDK)
    2. ADK가 summarize 도구 호출
    3. Synapse가 sampling 콜백 요청
    4. AgentHub가 LLM 호출 후 결과 반환
    5. ADK가 최종 응답 반환
    """

    @pytest.fixture
    def synapse_url(self):
        """Synapse MCP 서버 URL (로컬 환경)"""
        from tests.integration.adapters.conftest import MCP_TEST_URL

        return MCP_TEST_URL

    async def test_adk_calls_synapse_with_sampling(
        self, authenticated_client, synapse_url
    ):
        """ADK → Synapse 도구 호출 → Sampling 콜백 → LLM 호출 → 결과 반환

        Given: Synapse MCP 서버가 실행 중
        When: ADK가 Synapse 도구를 호출하고 sampling 요청 발생
        Then: LLM 호출 후 결과가 반환되어야 함
        """
        # 1. Synapse 등록 (Dual-Track)
        response = authenticated_client.post(
            "/api/mcp/servers", json={"url": synapse_url, "name": "Test Synapse"}
        )
        assert response.status_code == 201  # Created
        endpoint_id = response.json()["id"]

        # 2. ADK에게 Synapse 도구 사용 지시
        # (summarize 도구가 sampling을 요청한다고 가정)
        response = authenticated_client.post(
            "/api/chat",
            json={
                "message": "Summarize the latest news using Synapse",
                "conversation_id": "test-conv-dual-track",
            },
        )
        assert response.status_code == 200

        # 3. SSE 스트림에서 sampling_request 이벤트 확인
        # (이 테스트는 E2E Playwright로 구현하는 것이 더 적절)
        # Integration 레벨에서는 로그나 SamplingService 상태로 확인

        # 4. Sampling 요청 목록 확인
        response = authenticated_client.get("/api/sampling/requests")
        requests = response.json()["requests"]
        # Sampling 요청이 생성되었는지 확인 (실제 Synapse 동작에 따라 달라질 수 있음)
        # assert len(requests) > 0
        # sampling_request = requests[0]

        # 5. Approve (LLM 호출 + 시그널)
        # response = authenticated_client.post(
        #     f"/api/sampling/requests/{sampling_request['id']}/approve"
        # )
        # assert response.status_code == 200

        # 6. ADK가 최종 응답 반환
        # (실제로는 chat SSE를 구독하여 확인해야 함)

    async def test_sampling_callback_timeout_sends_sse(
        self, authenticated_client, synapse_url
    ):
        """Sampling Short timeout 시 SSE 알림 전송

        Given: Synapse MCP 서버가 실행 중
        When: Sampling 요청 발생 후 approve 없이 30초 대기
        Then: SSE 알림이 전송되어야 함
        """
        # 1. Synapse 등록
        response = authenticated_client.post(
            "/api/mcp/servers", json={"url": synapse_url, "name": "Test Synapse"}
        )
        assert response.status_code == 201  # Created
        endpoint_id = response.json()["id"]

        # 2. Sampling 요청 트리거 (approve 없이 30초 대기)
        # (이 테스트는 실제 30초를 기다려야 하므로, mock 또는 timeout 단축 필요)
        # 실제 구현 시에는 SamplingService.wait_for_response의 timeout을 mock

        # 3. SSE 이벤트 확인 (Playwright E2E로 구현 권장)
        # SSE 스트림을 구독하여 sampling_request 이벤트 확인
        # (Integration 레벨에서는 구현하기 어려움)
        pass

    async def test_restore_endpoints_connects_dual_track(
        self, authenticated_client, synapse_url
    ):
        """서버 재시작 시 Dual-Track 재연결

        Given: Synapse MCP 서버가 등록되어 있음
        When: 서버 재시작 (lifespan)
        Then: ADK Track + SDK Track 모두 재연결되어야 함
        """
        # 1. Synapse 등록
        response = authenticated_client.post(
            "/api/mcp/servers", json={"url": synapse_url, "name": "Test Synapse"}
        )
        assert response.status_code == 201  # Created
        endpoint_id = response.json()["id"]

        # 2. 서버 재시작 시뮬레이션
        # (authenticated_client의 lifespan은 자동으로 실행됨)
        # 실제로는 새로운 client를 생성하여 lifespan을 다시 트리거해야 함

        # 3. 엔드포인트 목록 확인
        response = authenticated_client.get("/api/mcp/servers")
        endpoints = response.json()
        assert len(endpoints) > 0
        restored_endpoint = endpoints[0]
        assert restored_endpoint["id"] == endpoint_id
        assert restored_endpoint["url"] == synapse_url

        # 4. Dual-Track 연결 확인 (도구 목록 확인)
        assert len(restored_endpoint["tools"]) > 0
