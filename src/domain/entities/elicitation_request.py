"""ElicitationRequest 엔티티

MCP Elicitation 요청을 표현합니다. 순수 Python으로 작성됩니다.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ElicitationAction(str, Enum):
    """Elicitation 액션"""

    ACCEPT = "accept"
    DECLINE = "decline"
    CANCEL = "cancel"


class ElicitationStatus(str, Enum):
    """Elicitation 요청 상태"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


@dataclass
class ElicitationRequest:
    """
    MCP Elicitation 요청

    MCP 서버가 사용자 입력을 요청할 때 사용됩니다.

    Attributes:
        id: 요청 ID
        endpoint_id: MCP 엔드포인트 ID
        message: 사용자에게 보여줄 메시지
        requested_schema: JSON Schema (입력 구조)
        action: 사용자 액션 (accept/decline/cancel)
        content: 사용자 입력 내용 (action=accept일 때)
        status: 요청 상태
        created_at: 생성 시각 (UTC)
    """

    id: str
    endpoint_id: str
    message: str
    requested_schema: dict[str, Any]
    action: ElicitationAction | None = None
    content: dict[str, Any] | None = None
    status: ElicitationStatus = ElicitationStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
