"""Prompt API Response Schemas"""

from pydantic import BaseModel

from src.domain.entities.prompt_template import PromptArgument, PromptTemplate


class PromptArgumentSchema(BaseModel):
    """PromptArgument 응답 스키마"""

    name: str
    required: bool = True
    description: str = ""

    @classmethod
    def from_entity(cls, arg: PromptArgument) -> "PromptArgumentSchema":
        """Domain Entity → HTTP Response Schema"""
        return cls(
            name=arg.name,
            required=arg.required,
            description=arg.description,
        )


class PromptTemplateSchema(BaseModel):
    """PromptTemplate 응답 스키마"""

    name: str
    description: str = ""
    arguments: list[PromptArgumentSchema]

    @classmethod
    def from_entity(cls, prompt: PromptTemplate) -> "PromptTemplateSchema":
        """Domain Entity → HTTP Response Schema"""
        return cls(
            name=prompt.name,
            description=prompt.description,
            arguments=[PromptArgumentSchema.from_entity(arg) for arg in prompt.arguments],
        )


class PromptListResponse(BaseModel):
    """Prompt 목록 응답"""

    prompts: list[PromptTemplateSchema]


class PromptContentRequest(BaseModel):
    """Prompt 렌더링 요청"""

    arguments: dict[str, str] = {}


class PromptContentResponse(BaseModel):
    """Prompt 렌더링 응답"""

    content: str
