"""Endpoint 엔티티 - MCP/A2A 서버 엔드포인트

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from src.domain.entities.enums import EndpointStatus, EndpointType
from src.domain.exceptions import InvalidUrlError

if TYPE_CHECKING:
    from src.domain.entities.auth_config import AuthConfig
    from src.domain.entities.tool import Tool


@dataclass
class Endpoint:
    """
    MCP/A2A 서버 엔드포인트

    외부 서버(MCP 또는 A2A)에 대한 연결 정보와 상태를 관리합니다.

    Attributes:
        url: 서버 URL (http:// 또는 https://)
        type: 엔드포인트 유형 (MCP 또는 A2A)
        name: 표시 이름 (없으면 URL에서 자동 추출)
        id: UUID 식별자
        enabled: 활성화 여부
        status: 연결 상태
        registered_at: 등록 시각
        last_health_check: 마지막 상태 확인 시각
        tools: 제공하는 도구 목록 (MCP only)
        agent_card: A2A Agent Card 정보 (A2A only)
        auth_config: 인증 설정 (선택적, MCP 서버용)

    Example:
        >>> endpoint = Endpoint(
        ...     url="https://mcp.example.com/",
        ...     type=EndpointType.MCP,
        ...     name="Example MCP Server"
        ... )
        >>> endpoint.update_status(EndpointStatus.CONNECTED)
    """

    url: str
    type: EndpointType
    name: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enabled: bool = True
    status: EndpointStatus = EndpointStatus.UNKNOWN
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_health_check: datetime | None = None
    tools: list["Tool"] = field(default_factory=list)
    agent_card: dict[str, Any] | None = None
    auth_config: "AuthConfig | None" = None

    def __post_init__(self) -> None:
        """생성 후 URL 유효성 검증 및 이름 자동 설정"""
        if not self.url:
            raise InvalidUrlError("URL cannot be empty")

        if not self.url.startswith(("http://", "https://")):
            raise InvalidUrlError(f"Invalid URL scheme: {self.url}")

        if not self.name:
            self.name = self._extract_name_from_url()

    def _extract_name_from_url(self) -> str:
        """URL에서 표시 이름 추출

        Returns:
            호스트명 (포트 포함)
        """
        parsed = urlparse(self.url)
        return parsed.netloc or self.url

    def update_status(self, status: EndpointStatus) -> None:
        """
        연결 상태 업데이트

        Args:
            status: 새로운 상태
        """
        self.status = status
        self.last_health_check = datetime.utcnow()

    def enable(self) -> None:
        """엔드포인트 활성화"""
        self.enabled = True

    def disable(self) -> None:
        """엔드포인트 비활성화"""
        self.enabled = False
