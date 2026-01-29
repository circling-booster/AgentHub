"""DI Container (dependency-injector)

Phase 2에서 Adapter providers 추가 예정:
- orchestrator_adapter
- dynamic_toolset
- storage adapters
"""

from dependency_injector import containers, providers

from src.config.settings import Settings


class Container(containers.DeclarativeContainer):
    """AgentHub 의존성 주입 컨테이너"""

    config = providers.Configuration()
    settings = providers.Singleton(Settings)
