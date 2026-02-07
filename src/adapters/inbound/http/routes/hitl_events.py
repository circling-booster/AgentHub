"""HITL SSE Events Stream API

TDD Step 6.5a: Green Phase
"""

import json

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.adapters.outbound.sse.broker import SseBroker
from src.config.container import Container

router = APIRouter(prefix="/api/hitl", tags=["hitl-events"])


@router.get("/events")
@inject
async def hitl_events_stream(
    sse_broker: SseBroker = Depends(Provide[Container.sse_broker]),
):
    """HITL 이벤트 SSE 스트림

    sampling_request, elicitation_request 이벤트를 실시간으로 수신합니다.
    """

    async def event_generator():
        """SSE 형식으로 이벤트 스트림 생성"""
        # Keep-alive ping: 연결 즉시 전송 (테스트 용이성 개선)
        yield ": ping\n\n"

        async for event in sse_broker.subscribe():
            # SSE 형식으로 전송
            event_type = event["type"]
            data = event["data"]
            yield f"event: {event_type}\n"
            yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx buffering 방지
        },
    )
