"""Application Settings (pydantic-settings)

환경변수 > .env > YAML > 기본값 우선순위로 설정 로드.
"""

import warnings

from pydantic import BaseModel, Field, field_validator
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

    default_model: str = "openai/gpt-4o-mini"
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

    max_active_tools: int = 100  # Step 11: 30 → 100
    defer_loading_threshold: int = 30  # Step 11: Defer loading 활성화 기준
    cache_ttl_seconds: int = 300
    max_retries: int = 2
    retry_backoff_seconds: float = 1.0


class ObservabilitySettings(BaseModel):
    """관찰성 설정 (Step 5-7: Part B)"""

    log_llm_requests: bool = True
    max_log_chars: int = 500
    log_format: str = "text"  # "text" or "json" (Step 7)


class GatewaySettings(BaseModel):
    """Gateway 설정 (Phase 6 Part A Step 2)"""

    rate_limit_rps: float = 5.0  # 초당 요청 제한
    burst_size: int = 10  # Token Bucket capacity
    circuit_failure_threshold: int = 5  # Circuit Breaker 실패 임계값
    circuit_recovery_timeout: float = 60.0  # Circuit Breaker 복구 대기 시간 (초)
    fallback_enabled: bool = True  # Fallback 서버 전환 활성화


class CostSettings(BaseModel):
    """비용 추적 설정 (Phase 6 Part A Step 3)"""

    monthly_budget_usd: float = 100.0  # 월별 예산 (USD)
    warning_threshold: float = 0.9  # 90%: 경고
    critical_threshold: float = 1.0  # 100%: 심각
    hard_limit_threshold: float = 1.1  # 110%: 차단


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
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    gateway: GatewaySettings = Field(default_factory=GatewaySettings)
    cost: CostSettings = Field(default_factory=CostSettings)

    # Phase 1: DEV_MODE support
    dev_mode: bool = False  # DEV_MODE=true 시 개발 모드 활성화

    @field_validator("dev_mode")
    @classmethod
    def warn_if_dev_mode_enabled(cls, v: bool) -> bool:
        """DEV_MODE 활성화 시 경고"""
        if v:
            warnings.warn(
                "DEV_MODE is enabled. This should ONLY be used in local development. "
                "NEVER deploy with DEV_MODE=true to production!",
                UserWarning,
                stacklevel=2,
            )
        return v

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
