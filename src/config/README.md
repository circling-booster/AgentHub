# Configuration Layer

> pydantic-settings 기반 설정 관리 및 의존성 주입

## Purpose

AgentHub의 환경 설정과 의존성 주입(DI)을 관리합니다.

## Structure

```
config/
├── __init__.py
├── settings.py     # pydantic-settings 기반 설정 (Phase 2에서 구현)
└── container.py    # dependency-injector DI 컨테이너 (Phase 2에서 구현)
```

## Settings Priority (계획)

설정 값은 다음 우선순위로 로드됩니다:

```
1. 환경변수 (최우선)
2. .env 파일
3. YAML 설정 파일 (configs/default.yaml)
4. 기본값
```

### 예시

```python
# src/config/settings.py (Phase 2 구현 예정)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        yaml_file="configs/default.yaml",
    )

    # 서버 설정
    server_host: str = "localhost"
    server_port: int = 8000

    # LLM 설정
    llm_default_model: str = "anthropic/claude-sonnet-4-20250514"
    llm_timeout: int = 120

    # 저장소 설정
    storage_data_dir: str = "./data"
    storage_database: str = "agenthub.db"

    # API 키 (환경변수에서만)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
```

### 환경변수 네이밍

```bash
# .env 파일 예시
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# 중첩 설정은 __ 구분자 사용
SERVER__HOST=0.0.0.0
SERVER__PORT=8080
LLM__DEFAULT_MODEL=openai/gpt-4
```

## Dependency Injection (계획)

```python
# src/config/container.py (Phase 2 구현 예정)
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    """의존성 주입 컨테이너"""

    config = providers.Configuration()
    settings = providers.Singleton(Settings)

    # Storage Adapters
    conversation_storage = providers.Singleton(
        SqliteConversationStorage,
        db_path=config.storage.database,
    )

    endpoint_storage = providers.Singleton(
        JsonEndpointStorage,
        data_dir=config.storage.data_dir,
    )

    # ADK Components
    dynamic_toolset = providers.Singleton(
        DynamicToolset,
        cache_ttl_seconds=300,
    )

    orchestrator_adapter = providers.Singleton(
        AdkOrchestratorAdapter,
        model=config.llm.default_model,
        dynamic_toolset=dynamic_toolset,
    )

    # Domain Services
    conversation_service = providers.Factory(
        ConversationService,
        storage=conversation_storage,
        orchestrator=orchestrator_adapter,
    )
```

## Usage (Phase 2 이후)

```python
# FastAPI에서 사용
from fastapi import Depends
from dependency_injector.wiring import inject, Provide

from src.config.container import Container

@router.post("/chat")
@inject
async def chat(
    request: ChatRequest,
    service: ConversationService = Depends(Provide[Container.conversation_service]),
):
    async for chunk in service.send_message(request.conversation_id, request.message):
        yield chunk
```

## Key Files (Phase 2 구현 예정)

| 파일 | 역할 |
|------|------|
| `settings.py` | 환경 설정 로드 (pydantic-settings) |
| `container.py` | 의존성 주입 컨테이너 (dependency-injector) |

## Configuration Files

```
project/
├── .env                    # 로컬 환경변수 (git ignore)
├── .env.example            # 환경변수 템플릿
└── configs/
    ├── default.yaml        # 기본 설정
    └── production.yaml     # 프로덕션 설정 (선택적)
```

## References

- [docs/implementation-guide.md](../../docs/implementation-guide.md) - 설정 관리 상세
- [pydantic-settings 문서](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [dependency-injector 문서](https://python-dependency-injector.ets-labs.org/)
