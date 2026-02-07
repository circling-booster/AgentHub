"""ElicitationService - Elicitation HITL 요청 큐 관리

asyncio.Event 기반 Signal 패턴으로 HITL 요청을 관리합니다.
SamplingService와 동일한 패턴 사용.
Domain 레이어 순수 Python (외부 라이브러리 의존 없음).
"""

import asyncio
from datetime import datetime, timezone

from src.domain.entities.elicitation_request import (
    ElicitationAction,
    ElicitationRequest,
    ElicitationStatus,
)


class ElicitationService:
    """Elicitation HITL 요청 큐 관리

    SamplingService와 동일한 Signal 패턴 사용.
    """

    def __init__(self, ttl_seconds: int = 600) -> None:
        """서비스 초기화

        Args:
            ttl_seconds: 요청 TTL (초, 기본 600초 = 10분)
        """
        self._requests: dict[str, ElicitationRequest] = {}
        self._events: dict[str, asyncio.Event] = {}
        self._ttl_seconds = ttl_seconds

    async def create_request(self, request: ElicitationRequest) -> None:
        """요청 생성 및 대기 이벤트 설정

        Args:
            request: ElicitationRequest 엔티티
        """
        self._requests[request.id] = request
        self._events[request.id] = asyncio.Event()

    def get_request(self, request_id: str) -> ElicitationRequest | None:
        """요청 조회

        Args:
            request_id: 요청 ID

        Returns:
            ElicitationRequest 또는 None
        """
        return self._requests.get(request_id)

    async def wait_for_response(
        self,
        request_id: str,
        timeout: float = 30.0,
    ) -> ElicitationRequest | None:
        """Long-polling 대기 (asyncio.Event)

        Args:
            request_id: 요청 ID
            timeout: 대기 시간 (초)

        Returns:
            업데이트된 ElicitationRequest 또는 None (timeout)
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

    async def respond(
        self,
        request_id: str,
        action: ElicitationAction,
        content: dict | None = None,
    ) -> bool:
        """Elicitation 응답 (accept/decline/cancel)

        Args:
            request_id: 요청 ID
            action: ACCEPT, DECLINE, CANCEL
            content: 사용자 입력 (ACCEPT 시 필수)

        Returns:
            성공 여부
        """
        if request_id not in self._requests:
            return False

        request = self._requests[request_id]
        request.action = action
        request.content = content

        if action == ElicitationAction.ACCEPT:
            request.status = ElicitationStatus.ACCEPTED
        elif action == ElicitationAction.DECLINE:
            request.status = ElicitationStatus.DECLINED
        elif action == ElicitationAction.CANCEL:
            request.status = ElicitationStatus.CANCELLED

        # Signal waiting callback
        if request_id in self._events:
            self._events[request_id].set()

        return True

    def list_pending(self) -> list[ElicitationRequest]:
        """대기 중인 요청 목록

        Returns:
            PENDING 상태인 요청 목록
        """
        return [req for req in self._requests.values() if req.status == ElicitationStatus.PENDING]

    async def cleanup_expired(self) -> int:
        """만료된 요청 정리

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
