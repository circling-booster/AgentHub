"""Application Settings (pydantic-settings)

환경변수 > .env > YAML > 기본값 우선순위로 설정 로드.
"""

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class ServerSettings(BaseModel):
    """서버 설정"""

    host: str = "localhost"
    port: int = 8000


class LLMSettings(BaseModel):
    """LLM 설정"""

    default_model: str = "anthropic/claude-sonnet-4-20250514"
    timeout: int = 120


class StorageSettings(BaseModel):
    """저장소 설정"""

    data_dir: str = "./data"
    database: str = "agenthub.db"


class HealthCheckSettings(BaseModel):
    """헬스체크 설정"""

    interval_seconds: int = 30
    timeout_seconds: int = 5


class McpSettings(BaseModel):
    """MCP 설정"""

    max_active_tools: int = 30
    cache_ttl_seconds: int = 300


class Settings(BaseSettings):
    """AgentHub 애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",  # SERVER__HOST 형태
        extra="ignore",
        yaml_file="configs/default.yaml",
    )

    server: ServerSettings = Field(default_factory=ServerSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    health_check: HealthCheckSettings = Field(default_factory=HealthCheckSettings)
    mcp: McpSettings = Field(default_factory=McpSettings)

    # API 키 (환경변수에서만, 플랫 필드 유지)
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """YAML 설정 소스 활성화"""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )
