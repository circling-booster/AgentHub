"""Chat Streaming Routes

SSE 스트리밍 기반 채팅 API
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from src.adapters.inbound.http.schemas.chat import ChatRequest
from src.config.container import Container
from src.domain.services.orchestrator_service import OrchestratorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/stream")
@inject
async def chat_stream(
    request: Request,
    body: ChatRequest,
    orchestrator: OrchestratorService = Depends(Provide[Container.orchestrator_service]),
):
    """
    SSE 스트리밍 채팅

    Args:
        request: FastAPI Request (연결 상태 확인용)
        body: 채팅 요청 (conversation_id, message)
        orchestrator: OrchestratorService (DI)

    Returns:
        SSE 스트리밍 응답

    Events:
        - data: {"type": "text", "content": "..."}
        - data: {"type": "done"}
        - data: {"type": "error", "message": "..."}
    """

    async def generate() -> AsyncIterator[str]:
        """SSE 이벤트 생성기"""
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

            async for chunk in orchestrator.send_message(
                conversation_id=conversation_id,
                message=body.message,
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

                # "text" 이벤트 전송
                event_data = json.dumps({"type": "text", "content": chunk})
                yield f"data: {event_data}\n\n"
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

        except Exception as e:
            # 에러 이벤트 전송
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
            error_data = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {error_data}\n\n"

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

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
