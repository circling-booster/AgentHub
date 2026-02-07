"""Resource 엔티티

MCP Resource를 표현합니다. 순수 Python으로 작성됩니다.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Resource:
    """
    MCP Resource 메타데이터

    MCP 서버가 제공하는 리소스의 메타 정보를 표현합니다.

    Attributes:
        uri: 리소스 URI (file://, http://, custom://)
        name: 리소스 이름
        description: 리소스 설명 (선택)
        mime_type: MIME 타입 (선택)
    """

    uri: str
    name: str
    description: str = ""
    mime_type: str = ""


@dataclass(frozen=True, slots=True)
class ResourceContent:
    """
    MCP Resource 콘텐츠

    리소스의 실제 내용을 표현합니다.
    텍스트 또는 바이너리 중 하나만 가집니다.

    Attributes:
        uri: 리소스 URI
        text: 텍스트 콘텐츠 (text 리소스)
        blob: 바이너리 콘텐츠 (blob 리소스)
        mime_type: MIME 타입
    """

    uri: str
    text: str | None = None
    blob: bytes | None = None
    mime_type: str = ""
