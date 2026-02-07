"""RegistryService - 엔드포인트 등록 관리 서비스

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

import logging

from src.domain.entities.auth_config import AuthConfig
from src.domain.entities.elicitation_request import ElicitationAction, ElicitationRequest
from src.domain.entities.endpoint import Endpoint
from src.domain.entities.enums import EndpointType
from src.domain.entities.sampling_request import SamplingRequest, SamplingStatus
from src.domain.entities.tool import Tool
from src.domain.exceptions import DuplicateEndpointError, EndpointNotFoundError, HitlTimeoutError
from src.domain.ports.outbound.a2a_port import A2aPort
from src.domain.ports.outbound.hitl_notification_port import HitlNotificationPort
from src.domain.ports.outbound.mcp_client_port import (
    ElicitationCallback,
    McpClientPort,
    SamplingCallback,
)
from src.domain.ports.outbound.orchestrator_port import OrchestratorPort
from src.domain.ports.outbound.storage_port import EndpointStoragePort
from src.domain.ports.outbound.toolset_port import ToolsetPort
from src.domain.services.elicitation_service import ElicitationService
from src.domain.services.gateway_service import GatewayService
from src.domain.services.sampling_service import SamplingService

logger = logging.getLogger(__name__)


class RegistryService:
    """
    엔드포인트 등록 관리 서비스 (Dual-Track: ADK + SDK)

    MCP/A2A 엔드포인트의 등록, 해제, 조회를 담당합니다.
    ToolsetPort를 통해 MCP 서버와 연결하고 (ADK Track),
    McpClientPort를 통해 SDK Track (Resources/Prompts/HITL)도 연결합니다.

    Attributes:
        _storage: 엔드포인트 저장소 포트
        _toolset: 도구셋 포트 (ADK Track - Tools)
        _a2a_client: A2A 클라이언트 포트 (A2A용, 선택)
        _orchestrator: 오케스트레이터 포트 (선택, A2A LLM 연결용)
        _mcp_client: MCP SDK Track 포트 (선택, Resources/Prompts/HITL)
        _sampling_service: Sampling HITL 큐 (선택)
        _elicitation_service: Elicitation HITL 큐 (선택)
        _hitl_notification: SSE 브로드캐스트 포트 (선택)
    """

    def __init__(
        self,
        storage: EndpointStoragePort,
        toolset: ToolsetPort,
        a2a_client: A2aPort | None = None,
        orchestrator: OrchestratorPort | None = None,
        gateway_service: GatewayService | None = None,
        # 신규 의존성 (Method C - Phase 5)
        mcp_client: McpClientPort | None = None,
        sampling_service: SamplingService | None = None,
        elicitation_service: ElicitationService | None = None,
        hitl_notification: HitlNotificationPort | None = None,
        # Timeout 설정 (H2 수정: 테스트에서 주입 가능)
        short_timeout: float = 30.0,
        long_timeout: float = 270.0,
    ) -> None:
        """
        Args:
            storage: 엔드포인트 저장소 포트
            toolset: 도구셋 포트 (ADK Track - Tools)
            a2a_client: A2A 클라이언트 포트 (선택, None이면 A2A 미지원)
            orchestrator: 오케스트레이터 포트 (선택, A2A LLM 연결용)
            gateway_service: Gateway 서비스 (선택, Phase 6 Part A Step 2)
            mcp_client: MCP SDK Track 어댑터 (신규, Resources/Prompts/HITL)
            sampling_service: Sampling HITL 큐 (신규)
            elicitation_service: Elicitation HITL 큐 (신규)
            hitl_notification: SSE 브로드캐스트 어댑터 (신규)
            short_timeout: Short timeout 초 (기본 30초, 테스트에서 조정 가능)
            long_timeout: Long timeout 초 (기본 270초, 테스트에서 조정 가능)
        """
        # 기존 코드
        self._storage = storage
        self._toolset = toolset
        self._a2a_client = a2a_client
        self._orchestrator = orchestrator
        self._gateway_service = gateway_service

        # 신규 (Phase 5 - Method C)
        self._mcp_client = mcp_client
        self._sampling_service = sampling_service
        self._elicitation_service = elicitation_service
        self._hitl_notification = hitl_notification
        self._short_timeout = short_timeout
        self._long_timeout = long_timeout

    async def register_endpoint(
        self,
        url: str,
        name: str | None = None,
        endpoint_type: EndpointType = EndpointType.MCP,
        auth_config: AuthConfig | None = None,
    ) -> Endpoint:
        """
        엔드포인트 등록

        MCP 또는 A2A 서버를 등록합니다.

        Args:
            url: 엔드포인트 URL
            name: 이름 (선택, 없으면 URL에서 추출)
            endpoint_type: 엔드포인트 타입 (MCP 또는 A2A, 기본값 MCP)
            auth_config: 인증 설정 (선택, Phase 5-B Step 7)

        Returns:
            등록된 엔드포인트 객체

        Raises:
            InvalidUrlError: 유효하지 않은 URL
            DuplicateEndpointError: 이미 등록된 URL
            EndpointConnectionError: 연결 실패
            ToolLimitExceededError: 도구 수 제한 초과 (MCP만)
            ValueError: A2A 클라이언트 미설정 상태에서 A2A 등록 시도
        """
        # 중복 URL 검사
        existing = await self._storage.list_endpoints()
        for ep in existing:
            if ep.url == url:
                raise DuplicateEndpointError(f"Endpoint already registered: {url}")

        # 엔드포인트 생성 (URL 검증은 Endpoint에서 수행)
        endpoint = Endpoint(
            url=url,
            type=endpoint_type,
            name=name or "",
            auth_config=auth_config,  # Phase 5-B Step 7
        )

        # 타입별 처리
        if endpoint_type == EndpointType.MCP:
            # ADK Track (기존 - Tools)
            tools = await self._toolset.add_mcp_server(endpoint)

            # 도구를 엔드포인트에 연결
            for tool in tools:
                endpoint.tools.append(
                    Tool(
                        name=tool.name,
                        description=tool.description,
                        input_schema=tool.input_schema,
                        endpoint_id=endpoint.id,
                    )
                )

            # Gateway Service에 엔드포인트 등록 (Phase 6 Part A Step 2)
            if self._gateway_service:
                self._gateway_service.register_endpoint(endpoint)

            # SDK Track (신규 - Resources/Prompts/Sampling/Elicitation)
            if self._mcp_client:
                try:
                    sampling_cb = self._create_sampling_callback(endpoint.id)
                    elicitation_cb = self._create_elicitation_callback(endpoint.id)
                    await self._mcp_client.connect(endpoint.id, url, sampling_cb, elicitation_cb)
                    logger.info(f"MCP endpoint {endpoint.id} connected: ADK Track + SDK Track")
                except Exception as e:
                    logger.warning(f"SDK Track connection failed for {endpoint.id}: {e}")
                    # ADK Track은 이미 성공했으므로 계속 진행

        elif endpoint_type == EndpointType.A2A:
            # A2A 클라이언트 확인
            if self._a2a_client is None:
                raise ValueError("A2A client not configured")

            # A2A Agent 등록 및 Agent Card 조회
            agent_card = await self._a2a_client.register_agent(endpoint)
            endpoint.agent_card = agent_card

            # LLM에 A2A 에이전트 연결 (orchestrator가 있는 경우만)
            if self._orchestrator:
                await self._orchestrator.add_a2a_agent(endpoint.id, url)

        # 저장
        await self._storage.save_endpoint(endpoint)

        return endpoint

    async def unregister_endpoint(self, endpoint_id: str) -> bool:
        """
        엔드포인트 등록 해제

        Args:
            endpoint_id: 해제할 엔드포인트 ID

        Returns:
            해제 성공 여부
        """
        # 엔드포인트 조회 (타입 확인용)
        endpoint = await self._storage.get_endpoint(endpoint_id)
        if not endpoint:
            return False

        # 타입별 해제 처리
        if endpoint.type == EndpointType.A2A:
            if self._a2a_client:
                await self._a2a_client.unregister_agent(endpoint_id)
            # LLM에서 A2A 에이전트 연결 해제 (orchestrator가 있는 경우만)
            if self._orchestrator:
                await self._orchestrator.remove_a2a_agent(endpoint_id)
        elif endpoint.type == EndpointType.MCP:
            # ADK Track 정리
            await self._toolset.remove_mcp_server(endpoint_id)

        # SDK Track 연결 해제 (신규 - Phase 5)
        if endpoint.type == EndpointType.MCP and self._mcp_client:
            await self._mcp_client.disconnect(endpoint_id)

        # 저장소에서 삭제
        return await self._storage.delete_endpoint(endpoint_id)

    async def list_endpoints(
        self,
        type_filter: str | None = None,
    ) -> list[Endpoint]:
        """
        엔드포인트 목록 조회

        Args:
            type_filter: 타입 필터 ('mcp', 'a2a', None=전체)

        Returns:
            엔드포인트 목록
        """
        return await self._storage.list_endpoints(type_filter=type_filter)

    async def get_endpoint(self, endpoint_id: str) -> Endpoint:
        """
        엔드포인트 조회

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            엔드포인트 객체

        Raises:
            EndpointNotFoundError: 엔드포인트를 찾을 수 없을 때
        """
        endpoint = await self._storage.get_endpoint(endpoint_id)
        if endpoint is None:
            raise EndpointNotFoundError(f"Endpoint not found: {endpoint_id}")
        return endpoint

    async def get_endpoint_tools(self, endpoint_id: str) -> list[Tool]:
        """
        엔드포인트의 도구 목록 조회

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            도구 목록

        Raises:
            EndpointNotFoundError: 엔드포인트를 찾을 수 없을 때
        """
        endpoint = await self.get_endpoint(endpoint_id)
        return endpoint.tools

    async def check_endpoint_health(self, endpoint_id: str) -> bool:
        """
        엔드포인트 상태 확인

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            정상 여부

        Raises:
            EndpointNotFoundError: 엔드포인트를 찾을 수 없을 때
        """
        # 엔드포인트 존재 확인
        await self.get_endpoint(endpoint_id)

        # 상태 확인
        return await self._toolset.health_check(endpoint_id)

    async def enable_endpoint(self, endpoint_id: str) -> bool:
        """
        엔드포인트 활성화

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            성공 여부
        """
        endpoint = await self._storage.get_endpoint(endpoint_id)
        if endpoint is None:
            return False

        endpoint.enable()
        await self._storage.save_endpoint(endpoint)
        return True

    async def disable_endpoint(self, endpoint_id: str) -> bool:
        """
        엔드포인트 비활성화

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            성공 여부
        """
        endpoint = await self._storage.get_endpoint(endpoint_id)
        if endpoint is None:
            return False

        endpoint.disable()
        await self._storage.save_endpoint(endpoint)
        return True

    async def restore_endpoints(self) -> dict[str, list[str]]:
        """
        서버 시작 시 저장된 엔드포인트 복원

        저장소에 있는 모든 엔드포인트를 재연결합니다.
        실패한 엔드포인트는 건너뛰고 계속 진행합니다.

        Returns:
            {"restored": [...], "failed": [...]} 딕셔너리
        """
        endpoints = await self._storage.list_endpoints()
        restored: list[str] = []
        failed: list[str] = []

        for endpoint in endpoints:
            try:
                if endpoint.type == EndpointType.MCP:
                    # ADK Track 재연결 (기존)
                    await self._toolset.add_mcp_server(endpoint)

                    # SDK Track 재연결 (M1 신규 - Phase 5)
                    if self._mcp_client:
                        try:
                            sampling_cb = self._create_sampling_callback(endpoint.id)
                            elicitation_cb = self._create_elicitation_callback(endpoint.id)
                            await self._mcp_client.connect(
                                endpoint.id, endpoint.url, sampling_cb, elicitation_cb
                            )
                        except Exception as e:
                            logger.warning(f"SDK Track restoration failed for {endpoint.id}: {e}")
                            # ADK Track은 이미 성공했으므로 계속 진행

                    restored.append(endpoint.url)

                elif endpoint.type == EndpointType.A2A:
                    # A2A 에이전트 재등록
                    if self._a2a_client and self._orchestrator:
                        agent_card = await self._a2a_client.register_agent(endpoint)
                        endpoint.agent_card = agent_card
                        await self._orchestrator.add_a2a_agent(endpoint.id, endpoint.url)
                        restored.append(endpoint.url)
                    else:
                        logger.warning(
                            f"A2A endpoint {endpoint.url} skipped: "
                            "a2a_client or orchestrator not configured"
                        )
                        failed.append(endpoint.url)

            except Exception as e:
                logger.warning(f"Failed to restore endpoint {endpoint.url}: {e}")
                failed.append(endpoint.url)

        logger.info(f"Endpoints restored: {len(restored)}, failed: {len(failed)}")
        return {"restored": restored, "failed": failed}

    def _create_sampling_callback(self, _endpoint_id: str) -> SamplingCallback:
        """Sampling 콜백 생성 (Method C 클로저)

        MCP SDK callback은 blocking(await)이므로, callback 내에서:
        1. SamplingRequest 생성 및 큐에 추가
        2. 30초 wait (Short timeout)
        3. Timeout 시 SSE 알림 전송 + 270초 wait (Long timeout)
        4. approve 시그널 수신하면 결과 반환
        5. Reject 또는 최종 timeout 시 예외 발생

        Route는 approve() 호출로 시그널만 전송 (LLM 호출 후).

        Args:
            _endpoint_id: 엔드포인트 ID (현재 미사용, 향후 확장용)
        """

        async def callback(
            request_id: str,
            endpoint_id: str,
            messages: list[dict],
            model_preferences: dict | None,
            system_prompt: str | None,
            max_tokens: int,
        ) -> dict:
            # 1. SamplingRequest 생성
            request = SamplingRequest(
                id=request_id,
                endpoint_id=endpoint_id,
                messages=messages,
                model_preferences=model_preferences,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
            )

            # 2. 큐에 추가
            if self._sampling_service:
                await self._sampling_service.create_request(request)
            else:
                raise HitlTimeoutError("SamplingService not configured")

            # 3. Short timeout (기본 30초, 테스트에서 조정 가능)
            result = await self._sampling_service.wait_for_response(
                request_id, timeout=self._short_timeout
            )

            # 4. Timeout 시 SSE 알림 전송
            if result is None:
                if self._hitl_notification:
                    await self._hitl_notification.notify_sampling_request(request)

                # 5. Long timeout (기본 270초, 테스트에서 조정 가능)
                result = await self._sampling_service.wait_for_response(
                    request_id, timeout=self._long_timeout
                )

            # 6. 여전히 None이거나 REJECTED → 예외
            if result is None or result.status == SamplingStatus.REJECTED:
                raise HitlTimeoutError(f"Sampling request {request_id} rejected or timed out")

            # 7. LLM 결과 반환 (MCP 서버에 전달)
            return result.llm_result

        return callback

    def _create_elicitation_callback(self, _endpoint_id: str) -> ElicitationCallback:
        """Elicitation 콜백 생성 (동일한 패턴)

        Args:
            _endpoint_id: 엔드포인트 ID (현재 미사용, 향후 확장용)
        """

        async def callback(
            request_id: str,
            endpoint_id: str,
            message: str,
            requested_schema: dict,
        ) -> dict:
            # 1. ElicitationRequest 생성
            request = ElicitationRequest(
                id=request_id,
                endpoint_id=endpoint_id,
                message=message,
                requested_schema=requested_schema,
            )

            # 2. 큐에 추가
            if self._elicitation_service:
                await self._elicitation_service.create_request(request)
            else:
                raise HitlTimeoutError("ElicitationService not configured")

            # 3. Short timeout (기본 30초, 테스트에서 조정 가능)
            result = await self._elicitation_service.wait_for_response(
                request_id, timeout=self._short_timeout
            )

            # 4. Timeout 시 SSE 알림 전송
            if result is None:
                if self._hitl_notification:
                    await self._hitl_notification.notify_elicitation_request(request)

                # 5. Long timeout (기본 270초, 테스트에서 조정 가능)
                result = await self._elicitation_service.wait_for_response(
                    request_id, timeout=self._long_timeout
                )

            # 6. 여전히 None이거나 DECLINE/CANCEL → 예외 (H3 수정: HitlTimeoutError 사용)
            if result is None:
                raise HitlTimeoutError(f"Elicitation request {request_id} timed out")

            if result.action in (ElicitationAction.DECLINE, ElicitationAction.CANCEL):
                raise HitlTimeoutError(f"Elicitation request {request_id} {result.action.value}")

            # 7. 사용자 입력 반환 (MCP 서버에 전달)
            return {
                "action": result.action.value,
                "content": result.content,
            }

        return callback
