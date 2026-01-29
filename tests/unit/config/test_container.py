"""
DI Container 및 Settings 스캐폴딩 테스트

TDD Phase: RED - 테스트 먼저 작성, 구현은 Phase A.1.4에서
"""

from src.config.container import Container
from src.config.settings import Settings


class TestSettings:
    """Settings 기본값 검증"""

    def test_default_server_host(self):
        """서버 호스트 기본값은 localhost"""
        settings = Settings()
        assert settings.server.host == "localhost"

    def test_default_server_port(self):
        """서버 포트 기본값은 8000"""
        settings = Settings()
        assert settings.server.port == 8000

    def test_settings_is_base_settings(self):
        """Settings는 pydantic BaseSettings 인스턴스"""
        from pydantic_settings import BaseSettings

        settings = Settings()
        assert isinstance(settings, BaseSettings)


class TestContainer:
    """DI Container 스캐폴딩 검증"""

    def test_container_provides_settings(self):
        """Container가 Settings 인스턴스를 제공"""
        container = Container()
        settings = container.settings()
        assert isinstance(settings, Settings)

    def test_settings_singleton(self):
        """Settings는 싱글톤 (동일 인스턴스 반환)"""
        container = Container()
        settings1 = container.settings()
        settings2 = container.settings()
        assert settings1 is settings2
