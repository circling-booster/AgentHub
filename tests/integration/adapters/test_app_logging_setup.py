"""FastAPI App Logging Setup Tests (TDD RED - Step 7)

Phase 4 Part B: Verify logging configuration is initialized on app startup
"""

import logging


def test_app_startup_initializes_logging(tmp_path):
    """앱 시작 시 로깅 설정이 초기화되어야 함"""
    # Given: Settings with log_format="text"
    from src.adapters.inbound.http.app import create_app
    from src.config.settings import Settings

    settings = Settings()
    settings.observability.log_format = "text"

    # When: create_app() 호출
    _ = create_app()  # noqa: F841

    # Then: 루트 로거가 설정되어야 함
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0


async def test_app_startup_uses_json_format_when_configured():
    """observability.log_format="json" 설정 시 JSON 포맷 사용"""
    # Given: 환경변수로 JSON 포맷 설정
    import os

    # 기존 핸들러 모두 제거
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    os.environ["OBSERVABILITY__LOG_FORMAT"] = "json"

    try:
        # When: create_app() + lifespan 호출
        from src.adapters.inbound.http.app import create_app
        from src.config.logging_config import JsonFormatter

        app = create_app()

        # Lifespan manually trigger
        async with app.router.lifespan_context(app):
            # Then: JsonFormatter가 사용되어야 함
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) > 0

            # JSON formatter 확인
            json_formatters = [
                h for h in root_logger.handlers if isinstance(h.formatter, JsonFormatter)
            ]
            assert len(json_formatters) > 0, (
                f"Expected JsonFormatter but got: {[type(h.formatter).__name__ for h in root_logger.handlers]}"
            )

    finally:
        # Cleanup
        if "OBSERVABILITY__LOG_FORMAT" in os.environ:
            del os.environ["OBSERVABILITY__LOG_FORMAT"]
