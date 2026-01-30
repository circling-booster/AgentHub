"""DI Container (dependency-injector)

Phase 2 확장:
- Storage Adapters (Step 2) ✅
- ADK Adapters (Step 3-4) ✅
- Domain Services (Step 6) ✅
"""

from dependency_injector import containers, providers

from src.adapters.outbound.a2a.a2a_client_adapter import A2aClientAdapter
from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter
from src.adapters.outbound.storage.json_endpoint_storage import JsonEndpointStorage
from src.adapters.outbound.storage.sqlite_conversation_storage import (
    SqliteConversationStorage,
)
from src.config.settings import Settings
from src.domain.services.conversation_service import ConversationService
from src.domain.services.orchestrator_service import OrchestratorService
from src.domain.services.registry_service import RegistryService


class Container(containers.DeclarativeContainer):
    """AgentHub 의존성 주입 컨테이너 - Phase 2"""

    wiring_config = containers.WiringConfiguration(packages=["src.adapters.inbound.http"])

    # Settings (Singleton)
    config = providers.Configuration()
    settings = providers.Singleton(Settings)

    # Storage Adapters
    endpoint_storage = providers.Singleton(
        JsonEndpointStorage,
        data_dir=settings.provided.storage.data_dir,
    )

    conversation_storage = providers.Singleton(
        SqliteConversationStorage,
        db_path=providers.Callable(
            lambda s: f"{s.storage.data_dir}/{s.storage.database}", settings
        ),
    )

    # ADK Adapters
    dynamic_toolset = providers.Singleton(
        DynamicToolset,
        cache_ttl_seconds=settings.provided.mcp.cache_ttl_seconds,
    )

    orchestrator_adapter = providers.Singleton(
        AdkOrchestratorAdapter,
        model=settings.provided.llm.default_model,
        dynamic_toolset=dynamic_toolset,
    )

    # A2A Adapter
    a2a_client_adapter = providers.Singleton(A2aClientAdapter)

    # Domain Services
    conversation_service = providers.Factory(
        ConversationService,
        orchestrator=orchestrator_adapter,
        storage=conversation_storage,
    )

    orchestrator_service = providers.Factory(
        OrchestratorService,
        conversation_service=conversation_service,
    )

    registry_service = providers.Factory(
        RegistryService,
        toolset=dynamic_toolset,
        storage=endpoint_storage,
        a2a_client=a2a_client_adapter,
    )
