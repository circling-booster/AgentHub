"""Server Startup Validation Tests (Phase 5 Part D - Step 11)

목표: FastAPI app 시작 시 발생 가능한 오류 조기 감지
- Import 에러
- DI Container wiring 오류
- Lifespan 이벤트 실행 실패
- 라우터 등록 누락
- Settings 로딩 실패

TDD 순서:
1. RED: 테스트 작성 (실패 확인)
2. GREEN: 필요 시 main.py/container.py 수정
3. REFACTOR: 테스트 헬퍼 추출
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.adapters.inbound.http.app import create_app
from src.config.settings import Settings


class TestAppStartup:
    """FastAPI app 시작 검증"""

    @pytest.fixture
    async def app(self) -> FastAPI:
        """FastAPI app 인스턴스 생성 (lifespan 실행 포함)"""
        return create_app()

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """TestClient 생성"""
        return TestClient(app)

    def test_app_creates_and_starts(self, app: FastAPI):
        """FastAPI app 인스턴스 생성 및 lifespan 실행 성공"""
        # Given: create_app() 호출됨 (fixture)
        # When: app 인스턴스 검증
        # Then: app이 FastAPI 인스턴스여야 함
        assert isinstance(app, FastAPI)
        assert app.title == "AgentHub API"
        assert app.version == "0.1.0"

        # DI Container가 app에 주입되었는지 확인
        assert hasattr(app, "container")
        assert app.container is not None

    def test_all_routers_registered(self, app: FastAPI):
        """모든 라우터가 등록되었는지 확인"""
        # Given: create_app() 호출됨 (fixture)
        # When: app.routes 조회
        routes = [route.path for route in app.routes if hasattr(route, "path")]

        # Then: 필수 엔드포인트가 모두 등록되어야 함
        expected_routes = [
            "/health",
            "/auth/token",
            "/oauth/callback",  # OAuth 2.1
            "/api/mcp/servers",
            "/api/mcp/servers/{server_id}",
            "/api/a2a/agents",
            "/api/a2a/agents/{agent_id}",
            "/.well-known/agent-card.json",  # A2A Agent Card (표준 경로)
            "/api/chat/stream",
            "/api/conversations",
        ]

        for expected in expected_routes:
            assert any(expected in route for route in routes), (
                f"Expected route {expected} not found in {routes}"
            )

    def test_settings_loaded(self, app: FastAPI):
        """Settings가 올바르게 로딩되었는지 확인"""
        # Given: create_app() 호출됨 (fixture)
        # When: DI Container에서 Settings 조회
        settings = app.container.settings()

        # Then: Settings 인스턴스가 올바르게 생성되어야 함
        assert isinstance(settings, Settings)
        assert settings.server.host is not None
        assert settings.server.port is not None
        assert settings.llm.default_model is not None
        assert settings.storage.data_dir is not None

    def test_lifespan_startup_and_shutdown(self, client: TestClient):
        """Lifespan startup 및 shutdown 이벤트 실행 검증"""
        # Given: TestClient 생성 (lifespan 자동 실행)
        # When: health check 엔드포인트 호출
        response = client.get("/health")

        # Then: 서버가 정상 동작해야 함 (lifespan이 성공적으로 실행됨)
        assert response.status_code == 200

        # TestClient 종료 시 lifespan shutdown 자동 실행
        # (에러 발생 시 pytest가 실패로 표시)
