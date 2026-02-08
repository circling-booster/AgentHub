"""SamplingService - Sampling HITL 요청 큐 관리 (Method C Signal 패턴)

asyncio.Event 기반 Signal 패턴으로 HITL 요청을 관리합니다.
Domain 레이어 순수 Python (외부 라이브러리 의존 없음).

Method C Signal 패턴:
1. create_request() → 요청 생성 + asyncio.Event 준비
2. wait_for_response(timeout) → Event.wait() (콜백에서 대기)
3. approve(request_id, llm_result) → Event.set() (Route에서 시그널)
4. 콜백이 깨어나서 결과 반환
"""

import asyncio
from datetime import datetime, timezone

from src.domain.entities.sampling_request import SamplingRequest, SamplingStatus


class SamplingService:
    """Sampling HITL 요청 큐 관리 (Method C Signal 패턴)

    Note:
    - McpClientPort를 직접 사용하지 않음
    - RegistryService가 콜백을 생성하여 MCP SDK에 전달
    - Route는 LLM 호출 후 approve()로 시그널 전송
    """

    def __init__(self, ttl_seconds: int = 600) -> None:
        """서비스 초기화

        Args:
            ttl_seconds: 요청 TTL (초, 기본 600초 = 10분)
        """
        self._requests: dict[str, SamplingRequest] = {}
        self._events: dict[str, asyncio.Event] = {}
        self._ttl_seconds = ttl_seconds

    async def create_request(self, request: SamplingRequest) -> None:
        """요청 생성 및 대기 이벤트 설정

        Args:
            request: SamplingRequest 엔티티
        """
        self._requests[request.id] = request
        self._events[request.id] = asyncio.Event()

    def get_request(self, request_id: str) -> SamplingRequest | None:
        """요청 조회

        Args:
            request_id: 요청 ID

        Returns:
            SamplingRequest 또는 None
        """
        return self._requests.get(request_id)

    async def wait_for_response(
        self,
        request_id: str,
        timeout: float = 30.0,
    ) -> SamplingRequest | None:
        """Long-polling 대기 (Method C 핵심)

        asyncio.Event를 대기하다가 approve() 또는 reject() 호출 시 깨어남.

        Args:
            request_id: 요청 ID
            timeout: 대기 시간 (초)

        Returns:
            업데이트된 SamplingRequest 또는 None (timeout)
        """
        if request_id not in self._events:
            return None

        try:
            await asyncio.wait_for(
                self._events[request_id].wait(),
                timeout=timeout,
            )
            return self._requests.get(request_id)
        except asyncio.TimeoutError:
            return None

    async def approve(self, request_id: str, llm_result: dict) -> bool:
        """요청 승인 및 LLM 결과 설정 (Method C Signal)

        Route에서 LLM 호출 후 이 메서드로 결과를 전달하면,
        wait_for_response()가 깨어나서 콜백에 결과 반환.

        Args:
            request_id: 요청 ID
            llm_result: LLM 응답 dict (role, content, model)

        Returns:
            성공 여부
        """
        if request_id not in self._requests:
            return False

        request = self._requests[request_id]
        request.status = SamplingStatus.APPROVED
        request.llm_result = llm_result

        # Signal waiting callback
        if request_id in self._events:
            self._events[request_id].set()

        return True

    async def reject(self, request_id: str, reason: str = "") -> bool:
        """요청 거부

        Args:
            request_id: 요청 ID
            reason: 거부 사유 (optional)

        Returns:
            성공 여부
        """
        if request_id not in self._requests:
            return False

        request = self._requests[request_id]
        request.status = SamplingStatus.REJECTED
        request.rejection_reason = reason

        # Signal waiting callback
        if request_id in self._events:
            self._events[request_id].set()

        return True

    def list_pending(self) -> list[SamplingRequest]:
        """대기 중인 요청 목록

        Returns:
            PENDING 상태인 요청 목록
        """
        return [req for req in self._requests.values() if req.status == SamplingStatus.PENDING]

    async def cleanup_expired(self) -> int:
        """만료된 요청 정리 (TTL 기반)

        Returns:
            제거된 요청 수
        """
        now = datetime.now(timezone.utc)
        expired_ids = [
            req_id
            for req_id, req in self._requests.items()
            if (now - req.created_at).total_seconds() > self._ttl_seconds
        ]

        for req_id in expired_ids:
            del self._requests[req_id]
            if req_id in self._events:
                del self._events[req_id]

        return len(expired_ids)
