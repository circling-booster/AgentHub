"""Settings 중첩 모델 검증

TDD Phase: RED - 테스트 먼저 작성
"""

from pydantic import BaseModel

from src.config.settings import (
    HealthCheckSettings,
    LLMSettings,
    McpSettings,
    ServerSettings,
    Settings,
    StorageSettings,
)


class TestNestedModels:
    """중첩 모델 구조 검증"""

    def test_server_settings_is_base_model(self):
        """ServerSettings는 BaseModel 인스턴스"""
        settings = ServerSettings()
        assert isinstance(settings, BaseModel)

    def test_llm_settings_defaults(self):
        """LLMSettings 기본값"""
        settings = LLMSettings()
        assert settings.default_model == "openai/gpt-4o-mini"
        assert settings.timeout == 120

    def test_storage_settings_defaults(self):
        """StorageSettings 기본값"""
        settings = StorageSettings()
        assert settings.data_dir == "./data"
        assert settings.database == "agenthub.db"

    def test_health_check_settings_defaults(self):
        """HealthCheckSettings 기본값"""
        settings = HealthCheckSettings()
        assert settings.interval_seconds == 30
        assert settings.timeout_seconds == 5

    def test_mcp_settings_defaults(self):
        """McpSettings 기본값"""
        settings = McpSettings()
        assert settings.max_active_tools == 30
        assert settings.cache_ttl_seconds == 300


class TestSettingsIntegration:
    """Settings 통합 검증"""

    def test_all_nested_models_present(self):
        """모든 중첩 모델이 존재"""
        settings = Settings()
        assert hasattr(settings, "server")
        assert hasattr(settings, "llm")
        assert hasattr(settings, "storage")
        assert hasattr(settings, "health_check")
        assert hasattr(settings, "mcp")

    def test_nested_models_are_base_models(self):
        """중첩 모델이 BaseModel 인스턴스"""
        settings = Settings()
        assert isinstance(settings.server, BaseModel)
        assert isinstance(settings.llm, BaseModel)
        assert isinstance(settings.storage, BaseModel)
        assert isinstance(settings.health_check, BaseModel)
        assert isinstance(settings.mcp, BaseModel)

    def test_api_keys_flat_structure(self):
        """API 키는 플랫 필드 유지"""
        settings = Settings()
        assert hasattr(settings, "anthropic_api_key")
        assert hasattr(settings, "openai_api_key")
        assert hasattr(settings, "google_api_key")

    def test_env_override(self, monkeypatch):
        """환경변수 오버라이드 동작"""
        monkeypatch.setenv("SERVER__HOST", "0.0.0.0")
        monkeypatch.setenv("SERVER__PORT", "9000")
        settings = Settings()
        assert settings.server.host == "0.0.0.0"
        assert settings.server.port == 9000

    def test_yaml_config_structure(self):
        """YAML 설정 파일 지원 확인 (파일이 있으면 로드)"""
        settings = Settings()
        # configs/default.yaml이 없어도 기본값으로 동작
        assert settings.server.host == "localhost"
        assert settings.server.port == 8000
