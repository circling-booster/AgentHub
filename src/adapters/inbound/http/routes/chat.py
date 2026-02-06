"""Chat Streaming Routes

SSE 스트리밍 기반 채팅 API
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from src.adapters.inbound.http.schemas.chat import ChatRequest, ChatStreamEvent
from src.config.container import Container
from src.domain.entities.stream_chunk import StreamChunk
from src.domain.exceptions import DomainException
from src.domain.services.orchestrator_service import OrchestratorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


async def _generate_chat_stream(
    request: Request,
    body: ChatRequest,
    orchestrator: OrchestratorService,
) -> AsyncIterator[str]:
    """
    공통 SSE 이벤트 생성기

    Args:
        request: FastAPI Request (연결 상태 확인용)
        body: 채팅 요청 (conversation_id, message, page_context)
        orchestrator: OrchestratorService

    Yields:
        SSE 포맷 문자열 (data: {...}\\n\\n)
    """
    conversation_id = body.conversation_id
    chunk_count = 0

    try:
        # conversation_id가 None이면 자동 생성 후 conversation_created 이벤트 전송
        if conversation_id is None:
            conversation = await orchestrator.create_conversation()
            conversation_id = conversation.id
            created_event = json.dumps(
                {"type": "conversation_created", "conversation_id": conversation_id}
            )
            yield f"data: {created_event}\n\n"
            logger.info(
                "Stream created",
                extra={
                    "conversation_id": conversation_id,
                    "lifecycle": "created",
                    "message_preview": body.message[:50] if body.message else "",
                },
            )
        else:
            logger.info(
                "Stream created",
                extra={
                    "conversation_id": conversation_id,
                    "lifecycle": "created",
                    "message_preview": body.message[:50] if body.message else "",
                },
            )

        logger.debug(
            "Stream streaming",
            extra={"conversation_id": conversation_id, "lifecycle": "streaming"},
        )

        # page_context를 dict로 변환
        page_context_dict = None
        if body.page_context:
            page_context_dict = body.page_context.model_dump()

        async for chunk in orchestrator.send_message(
            conversation_id=conversation_id,
            message=body.message,
            page_context=page_context_dict,
        ):
            # 클라이언트 연결 해제 확인 (Zombie Task 방지)
            if await request.is_disconnected():
                logger.warning(
                    "Client disconnected, stopping stream",
                    extra={
                        "conversation_id": conversation_id,
                        "lifecycle": "cancelled",
                        "chunks_sent": chunk_count,
                    },
                )
                break

            # StreamChunk → SSE 이벤트 전송
            event = ChatStreamEvent.from_stream_chunk(chunk)
            event_data = event.model_dump(exclude_none=True)
            yield f"data: {json.dumps(event_data)}\n\n"
            chunk_count += 1

        # "done" 이벤트 전송
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        logger.info(
            "Stream completed",
            extra={
                "conversation_id": conversation_id,
                "lifecycle": "completed",
                "chunks_sent": chunk_count,
            },
        )

    except asyncio.CancelledError:
        # 연결 해제 시 정리 로직
        logger.info(
            "Stream cancelled",
            extra={
                "conversation_id": conversation_id,
                "lifecycle": "cancelled",
                "chunks_sent": chunk_count,
            },
        )
        raise  # CancelledError는 다시 발생시켜야 함

    except DomainException as e:
        # 도메인 예외 → typed error 이벤트 전송
        logger.error(
            "Stream domain error",
            extra={
                "conversation_id": conversation_id,
                "lifecycle": "error",
                "chunks_sent": chunk_count,
                "error": str(e),
                "error_code": e.code,
            },
            exc_info=True,
        )
        error_chunk = StreamChunk.error(str(e), code=e.code)
        event = ChatStreamEvent.from_stream_chunk(error_chunk)
        yield f"data: {json.dumps(event.model_dump(exclude_none=True))}\n\n"

    except Exception as e:
        # 예상하지 못한 에러 → generic error 이벤트 전송
        logger.error(
            "Stream error",
            extra={
                "conversation_id": conversation_id,
                "lifecycle": "error",
                "chunks_sent": chunk_count,
                "error": str(e),
            },
            exc_info=True,
        )
        error_chunk = StreamChunk.error(str(e), code="UnknownError")
        event = ChatStreamEvent.from_stream_chunk(error_chunk)
        yield f"data: {json.dumps(event.model_dump(exclude_none=True))}\n\n"

    finally:
        # 리소스 정리 보장
        logger.debug(
            "Stream cleanup",
            extra={
                "conversation_id": conversation_id,
                "lifecycle": "cleanup",
                "chunks_sent": chunk_count,
            },
        )


@router.post("/stream")
@inject
async def chat_stream(
    request: Request,
    body: ChatRequest,
    orchestrator: OrchestratorService = Depends(Provide[Container.orchestrator_service]),
):
    """
    SSE 스트리밍 채팅 (POST - JSON body)

    Args:
        request: FastAPI Request (연결 상태 확인용)
        body: 채팅 요청 (conversation_id, message, page_context)
        orchestrator: OrchestratorService (DI)

    Returns:
        SSE 스트리밍 응답

    Events:
        - data: {"type": "text", "content": "..."}
        - data: {"type": "tool_call", "tool_name": "...", "tool_arguments": {...}}
        - data: {"type": "tool_result", "tool_name": "...", "result": "..."}
        - data: {"type": "agent_transfer", "agent_name": "..."}
        - data: {"type": "done"}
        - data: {"type": "error", "content": "...", "error_code": "..."}
    """
    return StreamingResponse(
        _generate_chat_stream(request, body, orchestrator),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/stream")
@inject
async def chat_stream_get(
    request: Request,
    message: str = Query(..., min_length=1, description="Chat message"),
    conversation_id: str | None = Query(None, description="Conversation ID (optional)"),
    orchestrator: OrchestratorService = Depends(Provide[Container.orchestrator_service]),
):
    """
    SSE 스트리밍 채팅 (GET - EventSource 지원)

    Args:
        request: FastAPI Request
        message: 채팅 메시지 (query parameter)
        conversation_id: 대화 ID (optional, query parameter)
        orchestrator: OrchestratorService (DI)

    Returns:
        SSE 스트리밍 응답

    Note:
        GET 메서드는 page_context를 지원하지 않습니다 (query param으로 전달 불가)
    """
    # ChatRequest 객체 생성 (page_context는 None)
    body = ChatRequest(message=message, conversation_id=conversation_id)

    return StreamingResponse(
        _generate_chat_stream(request, body, orchestrator),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
