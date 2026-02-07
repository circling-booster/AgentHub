"""Resource API Response Schemas"""

import base64

from pydantic import BaseModel

from src.domain.entities.resource import Resource, ResourceContent


class ResourceSchema(BaseModel):
    """Resource 응답 스키마"""

    uri: str
    name: str
    description: str
    mime_type: str | None = None

    @classmethod
    def from_entity(cls, resource: Resource) -> "ResourceSchema":
        """Domain Entity → HTTP Response Schema"""
        return cls(
            uri=str(resource.uri),  # AnyUrl → str 변환
            name=resource.name,
            description=resource.description,
            mime_type=resource.mime_type or None,  # 빈 문자열 → None
        )


class ResourceContentSchema(BaseModel):
    """ResourceContent 응답 스키마"""

    uri: str
    mime_type: str | None = None
    text: str | None = None
    blob: str | None = None  # Base64 인코딩된 바이너리

    @classmethod
    def from_entity(cls, content: ResourceContent) -> "ResourceContentSchema":
        """Domain Entity → HTTP Response Schema (Base64 인코딩)"""
        blob_str = None
        if content.blob:
            # blob가 이미 bytes인 경우와 str인 경우 모두 처리
            if isinstance(content.blob, bytes):
                blob_str = base64.b64encode(content.blob).decode("ascii")
            else:
                # 이미 base64 인코딩된 문자열인 경우
                blob_str = content.blob

        return cls(
            uri=str(content.uri),  # AnyUrl → str 변환
            mime_type=content.mime_type,
            text=content.text,
            blob=blob_str,
        )


class ResourceListResponse(BaseModel):
    """Resource 목록 응답"""

    resources: list[ResourceSchema]
