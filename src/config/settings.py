"""Application Settings (pydantic-settings)

환경변수 > .env > 기본값 우선순위로 설정 로드.
Phase 2에서 LLM, Storage, HealthCheck 설정 추가 예정.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """AgentHub 애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AGENTHUB_",
        extra="ignore",
    )

    server_host: str = "localhost"
    server_port: int = 8000
