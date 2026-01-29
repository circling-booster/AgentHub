"""DI Container (dependency-injector)

Phase 2 확장 계획:
- Storage Adapters (Step 2)
- ADK Adapters (Step 3-4)
- Domain Services (Step 4)
"""

from dependency_injector import containers, providers

from src.config.settings import Settings


class Container(containers.DeclarativeContainer):
    """AgentHub 의존성 주입 컨테이너 - Phase 2 확장"""

    wiring_config = containers.WiringConfiguration(packages=["src.adapters.inbound.http"])

    # Settings (Singleton)
    config = providers.Configuration()
    settings = providers.Singleton(Settings)

    # Storage Adapters (Phase 2 Step 2에서 구현)
    # endpoint_storage = providers.Singleton(...)
    # conversation_storage = providers.Singleton(...)

    # ADK Adapters (Phase 2 Step 3-4에서 구현)
    # dynamic_toolset = providers.Singleton(...)
    # orchestrator_adapter = providers.Singleton(...)

    # Domain Services (Phase 2 Step 4에서 구현)
    # conversation_service = providers.Factory(...)
    # orchestrator_service = providers.Factory(...)
    # registry_service = providers.Factory(...)
    # health_monitor_service = providers.Factory(...)
