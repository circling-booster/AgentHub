"""MCP Client Port - Resources/Prompts/HITL용 SDK 기반 클라이언트

이 포트는 MCP SDK를 사용한 클라이언트 구현을 추상화합니다.
콜백은 Domain 타입을 사용하며, Adapter에서 MCP SDK 타입으로 변환합니다.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from src.domain.entities.prompt_template import PromptTemplate
from src.domain.entities.resource import Resource, ResourceContent


class SamplingCallback(Protocol):
    """Sampling 콜백 프로토콜 (Domain 추상화)

    MCP SDK의 SamplingFnT를 Domain에서 사용 가능하게 추상화합니다.
    Adapter에서 MCP SDK 타입으로 변환합니다.
    """

    async def __call__(
        self,
        request_id: str,
        endpoint_id: str,
        messages: list[dict[str, Any]],
        model_preferences: dict[str, Any] | None,
        system_prompt: str | None,
        max_tokens: int,
    ) -> dict[str, Any]: ...


class ElicitationCallback(Protocol):
    """Elicitation 콜백 프로토콜 (Domain 추상화)"""

    async def __call__(
        self,
        request_id: str,
        endpoint_id: str,
        message: str,
        requested_schema: dict[str, Any],
    ) -> dict[str, Any]: ...


class McpClientPort(ABC):
    """MCP SDK 기반 클라이언트 포트 - Resources/Prompts/HITL용

    Note: 콜백은 Domain 타입을 사용합니다. Adapter에서 MCP SDK 타입으로 변환합니다.
    """

    @abstractmethod
    async def connect(
        self,
        endpoint_id: str,
        url: str,
        sampling_callback: SamplingCallback | None = None,
        elicitation_callback: ElicitationCallback | None = None,
    ) -> None:
        """MCP 서버에 연결

        Args:
            endpoint_id: 엔드포인트 ID
            url: MCP 서버 URL
            sampling_callback: Sampling HITL 콜백 (선택)
            elicitation_callback: Elicitation HITL 콜백 (선택)
        """
        pass

    @abstractmethod
    async def disconnect(self, endpoint_id: str) -> None:
        """특정 엔드포인트 연결 해제

        Args:
            endpoint_id: 엔드포인트 ID
        """
        pass

    @abstractmethod
    async def disconnect_all(self) -> None:
        """모든 엔드포인트 연결 해제 (서버 종료 시)"""
        pass

    @abstractmethod
    async def list_resources(self, endpoint_id: str) -> list[Resource]:
        """리소스 목록 조회

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            리소스 목록

        Raises:
            EndpointNotFoundError: 연결되지 않은 엔드포인트
        """
        pass

    @abstractmethod
    async def read_resource(self, endpoint_id: str, uri: str) -> ResourceContent:
        """리소스 내용 읽기

        Args:
            endpoint_id: 엔드포인트 ID
            uri: 리소스 URI

        Returns:
            리소스 콘텐츠

        Raises:
            EndpointNotFoundError: 연결되지 않은 엔드포인트
            ResourceNotFoundError: 존재하지 않는 리소스
        """
        pass

    @abstractmethod
    async def list_prompts(self, endpoint_id: str) -> list[PromptTemplate]:
        """프롬프트 템플릿 목록 조회

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            프롬프트 템플릿 목록

        Raises:
            EndpointNotFoundError: 연결되지 않은 엔드포인트
        """
        pass

    @abstractmethod
    async def get_prompt(self, endpoint_id: str, name: str, arguments: dict | None) -> str:
        """프롬프트 렌더링

        Args:
            endpoint_id: 엔드포인트 ID
            name: 프롬프트 이름
            arguments: 프롬프트 인자

        Returns:
            렌더링된 프롬프트 텍스트

        Raises:
            EndpointNotFoundError: 연결되지 않은 엔드포인트
            PromptNotFoundError: 존재하지 않는 프롬프트
        """
        pass
