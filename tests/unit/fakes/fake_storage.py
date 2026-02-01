"""Fake Storage Adapters - 인메모리 저장소

ConversationStoragePort와 EndpointStoragePort의 테스트용 구현입니다.
"""

from src.domain.entities.conversation import Conversation
from src.domain.entities.endpoint import Endpoint
from src.domain.entities.enums import EndpointStatus
from src.domain.entities.message import Message
from src.domain.entities.tool_call import ToolCall
from src.domain.ports.outbound.storage_port import (
    ConversationStoragePort,
    EndpointStoragePort,
)


class FakeConversationStorage(ConversationStoragePort):
    """
    인메모리 대화 저장소

    테스트용 ConversationStoragePort 구현입니다.
    dict를 사용하여 메모리에 데이터를 저장합니다.
    """

    def __init__(self) -> None:
        self.conversations: dict[str, Conversation] = {}
        self.messages: dict[str, list[Message]] = {}
        self.tool_calls: dict[str, list[ToolCall]] = {}

    async def save_conversation(self, conversation: Conversation) -> None:
        """대화 저장"""
        self.conversations[conversation.id] = conversation
        if conversation.id not in self.messages:
            self.messages[conversation.id] = []

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        """대화 조회"""
        return self.conversations.get(conversation_id)

    async def list_conversations(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Conversation]:
        """대화 목록 조회 (최신순)"""
        sorted_convs = sorted(
            self.conversations.values(),
            key=lambda c: c.updated_at,
            reverse=True,
        )
        return sorted_convs[offset : offset + limit]

    async def delete_conversation(self, conversation_id: str) -> bool:
        """대화 삭제"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            self.messages.pop(conversation_id, None)
            return True
        return False

    async def save_message(self, message: Message) -> None:
        """메시지 저장"""
        conv_id = message.conversation_id
        if conv_id not in self.messages:
            self.messages[conv_id] = []
        self.messages[conv_id].append(message)

    async def get_messages(
        self,
        conversation_id: str,
        limit: int | None = None,
    ) -> list[Message]:
        """대화의 메시지 조회"""
        messages = self.messages.get(conversation_id, [])
        if limit:
            return messages[-limit:]
        return messages

    async def save_tool_call(
        self,
        message_id: str,
        tool_call: ToolCall,
    ) -> None:
        """도구 호출 저장 (message_id로 그룹화)"""
        if message_id not in self.tool_calls:
            self.tool_calls[message_id] = []
        self.tool_calls[message_id].append(tool_call)

    async def get_tool_calls(
        self,
        conversation_id: str,
    ) -> list[ToolCall]:
        """대화의 모든 도구 호출 이력 조회 (모든 메시지의 tool_calls 합산)"""
        # conversation_id에 속한 모든 메시지의 tool_calls 수집
        all_tool_calls: list[ToolCall] = []
        messages = self.messages.get(conversation_id, [])
        for message in messages:
            message_tool_calls = self.tool_calls.get(message.id, [])
            all_tool_calls.extend(message_tool_calls)

        # 시간순 정렬
        all_tool_calls.sort(key=lambda tc: tc.created_at)
        return all_tool_calls

    def clear(self) -> None:
        """모든 데이터 초기화"""
        self.conversations.clear()
        self.messages.clear()
        self.tool_calls.clear()


class FakeEndpointStorage(EndpointStoragePort):
    """
    인메모리 엔드포인트 저장소

    테스트용 EndpointStoragePort 구현입니다.
    dict를 사용하여 메모리에 데이터를 저장합니다.
    """

    def __init__(self) -> None:
        self.endpoints: dict[str, Endpoint] = {}

    async def save_endpoint(self, endpoint: Endpoint) -> None:
        """엔드포인트 저장"""
        self.endpoints[endpoint.id] = endpoint

    async def get_endpoint(self, endpoint_id: str) -> Endpoint | None:
        """엔드포인트 조회"""
        return self.endpoints.get(endpoint_id)

    async def list_endpoints(
        self,
        type_filter: str | None = None,
    ) -> list[Endpoint]:
        """엔드포인트 목록 조회"""
        endpoints = list(self.endpoints.values())
        if type_filter:
            endpoints = [e for e in endpoints if e.type.value == type_filter]
        return endpoints

    async def delete_endpoint(self, endpoint_id: str) -> bool:
        """엔드포인트 삭제"""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            return True
        return False

    async def update_endpoint_status(
        self,
        endpoint_id: str,
        status: str,
    ) -> bool:
        """엔드포인트 상태 갱신"""
        if endpoint_id in self.endpoints:
            self.endpoints[endpoint_id].update_status(EndpointStatus(status))
            return True
        return False

    def clear(self) -> None:
        """모든 데이터 초기화"""
        self.endpoints.clear()
