"""StoragePort - 저장소 인터페이스

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.entities.conversation import Conversation
    from src.domain.entities.endpoint import Endpoint
    from src.domain.entities.message import Message


class ConversationStoragePort(ABC):
    """
    대화 저장소 포트

    대화 세션 및 메시지를 저장/조회하는 인터페이스입니다.

    구현체 예시:
    - SqliteConversationStorage (SQLite WAL)
    - FakeConversationStorage (테스트용)
    """

    @abstractmethod
    async def save_conversation(self, conversation: "Conversation") -> None:
        """
        대화 저장/갱신

        Args:
            conversation: 저장할 대화 객체
        """
        pass

    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> "Conversation | None":
        """
        대화 조회

        Args:
            conversation_id: 대화 ID

        Returns:
            대화 객체 또는 None (없는 경우)
        """
        pass

    @abstractmethod
    async def list_conversations(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> list["Conversation"]:
        """
        대화 목록 조회

        Args:
            limit: 최대 결과 수
            offset: 시작 위치

        Returns:
            대화 목록 (최신순)
        """
        pass

    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        대화 삭제

        Args:
            conversation_id: 삭제할 대화 ID

        Returns:
            삭제 성공 여부
        """
        pass

    @abstractmethod
    async def save_message(self, message: "Message") -> None:
        """
        메시지 저장

        Args:
            message: 저장할 메시지 객체
        """
        pass

    @abstractmethod
    async def get_messages(
        self,
        conversation_id: str,
        limit: int | None = None,
    ) -> list["Message"]:
        """
        대화의 메시지 조회

        Args:
            conversation_id: 대화 ID
            limit: 최대 결과 수 (None이면 전체)

        Returns:
            메시지 목록 (시간순)
        """
        pass

    async def get_conversation_with_messages(
        self,
        conversation_id: str,
    ) -> "Conversation | None":
        """
        대화와 메시지를 함께 조회 (Aggregate Root 완전 로딩)

        기본 구현은 get_conversation + get_messages를 순차 호출합니다.
        서브클래스에서 최적화된 단일 쿼리로 오버라이드할 수 있습니다.

        Args:
            conversation_id: 대화 ID

        Returns:
            메시지가 포함된 대화 객체 또는 None
        """
        conversation = await self.get_conversation(conversation_id)
        if conversation is None:
            return None
        conversation.messages = await self.get_messages(conversation_id)
        return conversation


class EndpointStoragePort(ABC):
    """
    엔드포인트 저장소 포트

    MCP/A2A 엔드포인트를 저장/조회하는 인터페이스입니다.

    구현체 예시:
    - JsonEndpointStorage (JSON 파일)
    - FakeEndpointStorage (테스트용)
    """

    @abstractmethod
    async def save_endpoint(self, endpoint: "Endpoint") -> None:
        """
        엔드포인트 저장/갱신

        Args:
            endpoint: 저장할 엔드포인트 객체
        """
        pass

    @abstractmethod
    async def get_endpoint(self, endpoint_id: str) -> "Endpoint | None":
        """
        엔드포인트 조회

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            엔드포인트 객체 또는 None
        """
        pass

    @abstractmethod
    async def list_endpoints(
        self,
        type_filter: str | None = None,
    ) -> list["Endpoint"]:
        """
        엔드포인트 목록 조회

        Args:
            type_filter: 타입 필터 ('mcp', 'a2a', None=전체)

        Returns:
            엔드포인트 목록
        """
        pass

    @abstractmethod
    async def delete_endpoint(self, endpoint_id: str) -> bool:
        """
        엔드포인트 삭제

        Args:
            endpoint_id: 삭제할 엔드포인트 ID

        Returns:
            삭제 성공 여부
        """
        pass

    @abstractmethod
    async def update_endpoint_status(
        self,
        endpoint_id: str,
        status: str,
    ) -> bool:
        """
        엔드포인트 상태 갱신

        Args:
            endpoint_id: 엔드포인트 ID
            status: 새 상태 ('connected', 'disconnected', 'error', 'unknown')

        Returns:
            갱신 성공 여부
        """
        pass
