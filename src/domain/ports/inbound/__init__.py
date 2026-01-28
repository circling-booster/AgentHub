"""Inbound Ports (Driving Ports) - 외부에서 도메인으로 들어오는 인터페이스

외부 시스템(HTTP API, CLI 등)이 도메인 서비스에 접근하기 위한 인터페이스입니다.
도메인 서비스가 이 인터페이스들을 구현합니다.
"""

from src.domain.ports.inbound.chat_port import ChatPort
from src.domain.ports.inbound.management_port import ManagementPort

__all__ = [
    "ChatPort",
    "ManagementPort",
]
