"""Conversation CRUD Routes

대화 세션 관리 API (Phase 2.5 Extension 사이드패널용)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from src.adapters.inbound.http.schemas.conversations import (
    ConversationResponse,
    CreateConversationRequest,
)
from src.config.container import Container
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
