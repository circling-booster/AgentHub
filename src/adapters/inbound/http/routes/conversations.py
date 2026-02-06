"""Conversation CRUD Routes

대화 세션 관리 API (Phase 2.5 Extension 사이드패널용)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.adapters.inbound.http.schemas.conversations import (
    ConversationResponse,
    CreateConversationRequest,
)
from src.config.container import Container
from src.domain.ports.outbound.storage_port import ConversationStoragePort
from src.domain.services.conversation_service import ConversationService

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.post("", status_code=201, response_model=ConversationResponse)
@inject
async def create_conversation(
    body: CreateConversationRequest,
    conversation_service: ConversationService = Depends(Provide[Container.conversation_service]),
):
    """대화 생성"""
    conversation = await conversation_service.create_conversation(title=body.title)
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at.isoformat(),
    )


@router.get("", response_model=list[ConversationResponse])
@inject
async def list_conversations(
    limit: int = Query(default=20, ge=1, le=100),
    conversation_service: ConversationService = Depends(Provide[Container.conversation_service]),
):
    """대화 목록 조회 (최신순)"""
    conversations = await conversation_service.list_conversations(limit=limit)
    return [
        ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at.isoformat(),
        )
        for conv in conversations
    ]


@router.get("/{conversation_id}/tool-calls")
@inject
async def get_tool_calls(
    conversation_id: str,
    storage: ConversationStoragePort = Depends(Provide[Container.conversation_storage]),
):
    """대화의 도구 호출 이력 조회"""
    # 대화 존재 여부 확인
    conversation = await storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # ToolCall 조회
    tool_calls = await storage.get_tool_calls(conversation_id)

    # Pydantic 모델로 변환
    return [
        {
            "id": tc.id,
            "tool_name": tc.tool_name,
            "arguments": tc.arguments,
            "result": tc.result,
            "error": tc.error,
            "duration_ms": tc.duration_ms,
            "created_at": tc.created_at.isoformat(),
        }
        for tc in tool_calls
    ]


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_conversation(
    conversation_id: str,
    conversation_service: ConversationService = Depends(Provide[Container.conversation_service]),
):
    """
    대화 삭제

    Args:
        conversation_id: 대화 ID
        conversation_service: ConversationService (DI)

    Returns:
        204 No Content

    Raises:
        HTTPException(404): 대화를 찾을 수 없음
    """
    # 대화 삭제 (존재 여부 확인 포함)
    success = await conversation_service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
