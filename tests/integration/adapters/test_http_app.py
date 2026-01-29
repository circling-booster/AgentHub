"""
Integration tests for HTTP application setup (CORS, middleware order, API protection)

TDD Phase: RED - Tests written before implementation
"""

import pytest


class TestCorsConfiguration:
    """CORS 설정 통합 테스트 (chrome-extension:// Origin만 허용)"""

    @pytest.fixture
    def client(self, http_client):
        """TestClient fixture"""
        return http_client

    def test_cors_allows_chrome_extension_origin(self, client):
        """chrome-extension:// Origin에서 CORS 허용"""
        response = client.options(
            "/api/chat/stream",
            headers={
                "Origin": "chrome-extension://abcdefghijklmnop",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-Extension-Token,Content-Type",
            },
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        # allow-origin은 실제 Origin 또는 * 반환
        allowed_origin = response.headers.get("access-control-allow-origin")
        assert allowed_origin == "chrome-extension://abcdefghijklmnop" or allowed_origin == "*"

    def test_cors_blocks_web_origin(self, client):
        """일반 웹 Origin에서 CORS 차단"""
        response = client.options(
            "/api/chat/stream",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "POST",
            },
        )

        # CORS 차단 시 200이지만 Allow-Origin 헤더 없음
        # 또는 403/400 반환
        if response.status_code == 200:
            assert "access-control-allow-origin" not in response.headers
        else:
            assert response.status_code in [400, 403]

    def test_preflight_options_handled(self, client):
        """OPTIONS preflight 요청 처리"""
        response = client.options(
            "/api/mcp/servers",
            headers={
                "Origin": "chrome-extension://valid",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        assert response.status_code == 200

    def test_cors_allows_required_methods(self, client):
        """CORS가 필요한 HTTP 메서드 허용 (GET, POST, DELETE)"""
        response = client.options(
            "/api/chat/stream",
            headers={
                "Origin": "chrome-extension://test",
                "Access-Control-Request-Method": "POST",
            },
        )

        assert response.status_code == 200
        allowed_methods = response.headers.get("access-control-allow-methods", "")
        assert "POST" in allowed_methods.upper()

    def test_cors_allows_required_headers(self, client):
        """CORS가 필요한 헤더 허용 (X-Extension-Token, Content-Type)"""
        response = client.options(
            "/api/chat/stream",
            headers={
                "Origin": "chrome-extension://test",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-Extension-Token,Content-Type",
            },
        )

        assert response.status_code == 200
        allowed_headers = response.headers.get("access-control-allow-headers", "")
        assert "x-extension-token" in allowed_headers.lower()
        assert "content-type" in allowed_headers.lower()


class TestMiddlewareOrder:
    """Middleware 순서 통합 테스트 (CORS → Auth)

    FastAPI/Starlette는 add_middleware()를 insert(0, ...)로 처리하므로
    나중에 추가된 미들웨어가 outermost(먼저 실행)됩니다.
    CORS가 Auth보다 먼저 실행되어야 403 응답에도 CORS 헤더가 포함됩니다.

    회귀 테스트: CORS 헤더가 에러 응답에도 포함되는지 검증
    """

    @pytest.fixture
    def client(self, http_client):
        """TestClient fixture"""
        return http_client

    def test_middleware_order_cors_before_auth(self, client):
        """CORS 미들웨어가 Auth 미들웨어보다 먼저 실행"""
        # OPTIONS 요청은 Auth를 거치지 않고 CORS만 처리
        response = client.options(
            "/api/chat/stream",
            headers={
                "Origin": "chrome-extension://test",
                "Access-Control-Request-Method": "POST",
            },
        )

        # Auth 미들웨어가 먼저면 403, CORS가 먼저면 200
        assert response.status_code == 200

    def test_cors_headers_on_403_response(self, client):
        """토큰 없이 /api/* 호출 시 403 + CORS 헤더 포함 확인

        회귀 테스트: Middleware 순서가 잘못되면 Auth가 CORS보다
        먼저 실행되어 403 응답에 CORS 헤더가 누락됨.
        브라우저는 CORS 에러로 표시하여 실제 403을 디버깅하기 어려워짐.
        """
        response = client.post(
            "/api/chat/stream",
            json={"message": "test"},
            headers={"Origin": "chrome-extension://testextensionid"},
        )

        assert response.status_code == 403
        # CORS 헤더가 403 응답에도 포함되어야 함
        assert "access-control-allow-origin" in response.headers

    def test_non_extension_origin_rejected_on_post(self, client):
        """chrome-extension:// 이외 Origin의 POST 요청은 CORS 허용하지 않음"""
        response = client.post(
            "/api/chat/stream",
            json={"message": "test"},
            headers={"Origin": "http://malicious-site.com"},
        )

        # 악성 Origin에 CORS 헤더를 포함하지 않아야 함
        assert "access-control-allow-origin" not in response.headers


class TestApiProtection:
    """API 엔드포인트 보호 통합 테스트 (토큰 필수)"""

    @pytest.fixture
    def client(self, http_client):
        """TestClient fixture"""
        return http_client

    def test_api_endpoint_requires_token(self, client):
        """모든 /api/* 엔드포인트가 토큰 필요"""
        # 토큰 없이 요청
        response = client.post(
            "/api/chat/stream",
            json={"conversation_id": "test", "message": "hello"},
        )

        assert response.status_code == 403

    def test_api_endpoint_with_valid_token_accessible(self, client):
        """올바른 토큰으로 /api/* 접근 가능"""
        # 먼저 토큰 획득
        token_response = client.post(
            "/auth/token",
            json={"extension_id": "test"},
            headers={"Origin": "chrome-extension://test"},
        )
        assert token_response.status_code == 200
        token = token_response.json()["token"]

        # 토큰으로 API 호출
        response = client.post(
            "/api/chat/stream",
            json={"conversation_id": "test", "message": "hello"},
            headers={"X-Extension-Token": token},
        )

        # 구현 전이므로 404나 500일 수 있지만 403은 아님
        assert response.status_code != 403

    def test_public_endpoints_no_token_required(self, client):
        """공개 엔드포인트는 토큰 불필요 (/health, /auth/token)"""
        # /health
        health_response = client.get("/health")
        assert health_response.status_code == 200

        # /auth/token
        auth_response = client.post(
            "/auth/token",
            json={"extension_id": "test"},
            headers={"Origin": "chrome-extension://test"},
        )
        assert auth_response.status_code == 200


class TestLifespan:
    """FastAPI Lifespan 동작 검증

    TDD Phase: RED - 커스텀 lifespan 함수가 설정되었는지 검증
    deprecated @app.on_event("startup") 대신 asynccontextmanager 패턴 사용
    """

    def test_app_has_custom_lifespan(self):
        """create_app()이 커스텀 lifespan 함수를 사용"""
        from src.adapters.inbound.http.app import create_app

        app = create_app()
        # FastAPI가 lifespan을 _merge_lifespan_context로 래핑하므로
        # lifespan_context가 기본값(None)이 아닌지 확인
        assert app.router.lifespan_context is not None
        # merged_lifespan 래퍼가 설정되어야 함
        assert "merged_lifespan" in app.router.lifespan_context.__name__

    def test_health_endpoint_after_startup(self, http_client):
        """startup 후 /health 정상 응답"""
        response = http_client.get("/health")
        assert response.status_code == 200
