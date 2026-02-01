"""HealthMonitorService - 엔드포인트 상태 모니터링 서비스

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

import asyncio
import contextlib
import logging

from src.domain.entities.enums import EndpointStatus, EndpointType
from src.domain.ports.outbound.a2a_port import A2aPort
from src.domain.ports.outbound.storage_port import EndpointStoragePort
from src.domain.ports.outbound.toolset_port import ToolsetPort

logger = logging.getLogger(__name__)


class HealthMonitorService:
    """
    엔드포인트 상태 모니터링 서비스

    주기적으로 등록된 모든 엔드포인트의 상태를 확인하고
    상태를 갱신합니다.

    Attributes:
        _storage: 엔드포인트 저장소 포트
        _toolset: 도구셋 포트 (MCP health check)
        _a2a_client: A2A 클라이언트 포트 (A2A health check, optional)
        _check_interval: 확인 주기 (초)
        _running: 실행 중 여부
        _task: 백그라운드 작업
    """

    def __init__(
        self,
        storage: EndpointStoragePort,
        toolset: ToolsetPort,
        a2a_client: A2aPort | None = None,
        check_interval_seconds: int = 30,
    ) -> None:
        """
        Args:
            storage: 엔드포인트 저장소 포트
            toolset: 도구셋 포트 (MCP health check)
            a2a_client: A2A 클라이언트 포트 (optional)
            check_interval_seconds: 상태 확인 주기 (초)
        """
        self._storage = storage
        self._toolset = toolset
        self._a2a_client = a2a_client
        self._check_interval = check_interval_seconds
        self._running = False
        self._task: asyncio.Task | None = None

    @property
    def is_running(self) -> bool:
        """모니터 실행 중 여부"""
        return self._running

    async def start(self) -> None:
        """
        모니터링 시작

        백그라운드 태스크로 주기적 상태 확인을 시작합니다.
        """
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitor started (interval=%ds)", self._check_interval)

    async def stop(self) -> None:
        """
        모니터링 중지

        백그라운드 태스크를 취소하고 종료를 기다립니다.
        """
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        logger.info("Health monitor stopped")

    async def _monitor_loop(self) -> None:
        """모니터링 루프"""
        # 시작 시 즉시 한 번 확인
        await self.check_all_endpoints()

        while self._running:
            try:
                await asyncio.sleep(self._check_interval)
                if self._running:  # sleep 후 다시 확인
                    await self.check_all_endpoints()
            except asyncio.CancelledError:
                logger.info("Health monitor loop cancelled")
                break

    async def check_all_endpoints(self) -> dict[str, bool]:
        """
        모든 활성화된 엔드포인트 상태 확인

        Returns:
            엔드포인트 ID -> 상태 결과 매핑
        """
        endpoints = await self._storage.list_endpoints()
        results: dict[str, bool] = {}

        for endpoint in endpoints:
            # 비활성화된 엔드포인트는 건너뜀
            if not endpoint.enabled:
                continue

            # 타입별 health check
            if endpoint.type == EndpointType.MCP:
                is_healthy = await self._toolset.health_check(endpoint.id)
            elif endpoint.type == EndpointType.A2A:
                if self._a2a_client:
                    is_healthy = await self._a2a_client.health_check(endpoint.id)
                else:
                    is_healthy = False
            else:
                is_healthy = False

            results[endpoint.id] = is_healthy

            # 상태 갱신
            new_status = EndpointStatus.CONNECTED if is_healthy else EndpointStatus.ERROR
            endpoint.update_status(new_status)
            await self._storage.save_endpoint(endpoint)

        return results

    async def check_endpoint(self, endpoint_id: str) -> bool:
        """
        단일 엔드포인트 상태 확인

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            정상 여부 (엔드포인트가 없으면 False)
        """
        endpoint = await self._storage.get_endpoint(endpoint_id)
        if endpoint is None:
            return False

        # 타입별 health check
        if endpoint.type == EndpointType.MCP:
            is_healthy = await self._toolset.health_check(endpoint_id)
        elif endpoint.type == EndpointType.A2A:
            if self._a2a_client:
                is_healthy = await self._a2a_client.health_check(endpoint_id)
            else:
                is_healthy = False
        else:
            is_healthy = False

        # 상태 갱신
        new_status = EndpointStatus.CONNECTED if is_healthy else EndpointStatus.ERROR
        endpoint.update_status(new_status)
        await self._storage.save_endpoint(endpoint)

        return is_healthy
