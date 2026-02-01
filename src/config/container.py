"""DI Container (dependency-injector)

Phase 2 확장:
- Storage Adapters (Step 2) ✅
- ADK Adapters (Step 3-4) ✅
- Domain Services (Step 6) ✅
"""

from dependency_injector import containers, providers

from src.adapters.outbound.a2a.a2a_client_adapter import A2aClientAdapter
from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.adapters.outbound.adk.gateway_toolset import GatewayToolset
from src.adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter
from src.adapters.outbound.storage.json_endpoint_storage import JsonEndpointStorage
from src.adapters.outbound.storage.sqlite_conversation_storage import (
    SqliteConversationStorage,
)
from src.config.settings import Settings
from src.domain.services.conversation_service import ConversationService
from src.domain.services.gateway_service import GatewayService
from src.domain.services.health_monitor_service import HealthMonitorService
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
        settings=settings,
    )

    # Gateway Service (Phase 6 Part A Step 2)
    gateway_service = providers.Singleton(
        GatewayService,
        rate_limit_rps=settings.provided.gateway.rate_limit_rps,
        burst_size=settings.provided.gateway.burst_size,
        circuit_failure_threshold=settings.provided.gateway.circuit_failure_threshold,
        circuit_recovery_timeout=settings.provided.gateway.circuit_recovery_timeout,
    )

    # Gateway Toolset - DynamicToolset을 Circuit Breaker + Rate Limiting으로 래핑
    gateway_toolset = providers.Singleton(
        GatewayToolset,
        dynamic_toolset=dynamic_toolset,
        gateway_service=gateway_service,
    )

    orchestrator_adapter = providers.Singleton(
        AdkOrchestratorAdapter,
        model=settings.provided.llm.default_model,
        dynamic_toolset=gateway_toolset,  # ⚠️ GatewayToolset으로 교체 (LLM 보호)
        enable_llm_logging=settings.provided.observability.log_llm_requests,
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
        orchestrator=orchestrator_adapter,
        gateway_service=gateway_service,  # Phase 6 Part A Step 2
    )

    health_monitor_service = providers.Factory(
        HealthMonitorService,
        storage=endpoint_storage,
        toolset=dynamic_toolset,
        a2a_client=a2a_client_adapter,
        check_interval_seconds=settings.provided.health_check.interval_seconds,
    )
