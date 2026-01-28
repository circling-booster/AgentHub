"""Agent 엔티티 테스트"""

import uuid

import pytest

from src.domain.entities.agent import Agent
from src.domain.exceptions import ValidationError


class TestAgent:
    """Agent 엔티티 테스트"""

    def test_create_agent_with_required_fields(self):
        """필수 필드로 Agent 생성"""
        # When
        agent = Agent(name="TestAgent")

        # Then
        assert agent.name == "TestAgent"
        assert agent.model == "anthropic/claude-sonnet-4-20250514"
        assert "helpful assistant" in agent.instruction
        assert agent.id is not None

    def test_create_agent_with_custom_values(self):
        """커스텀 값으로 Agent 생성"""
        # When
        agent = Agent(
            name="CustomAgent",
            model="openai/gpt-4",
            instruction="You are a code reviewer.",
            id="agent-123",
        )

        # Then
        assert agent.name == "CustomAgent"
        assert agent.model == "openai/gpt-4"
        assert agent.instruction == "You are a code reviewer."
        assert agent.id == "agent-123"

    def test_agent_id_is_uuid_format(self):
        """기본 ID는 UUID 형식"""
        # When
        agent = Agent(name="Test")

        # Then
        try:
            uuid.UUID(agent.id)
            is_valid_uuid = True
        except ValueError:
            is_valid_uuid = False
        assert is_valid_uuid

    def test_empty_name_raises_validation_error(self):
        """빈 이름은 ValidationError 발생"""
        # When / Then
        with pytest.raises(ValidationError) as exc_info:
            Agent(name="")

        assert "name" in str(exc_info.value.message).lower()

    def test_default_model_is_claude(self):
        """기본 모델은 Claude"""
        # When
        agent = Agent(name="Test")

        # Then
        assert "claude" in agent.model.lower()
        assert "anthropic" in agent.model.lower()

    def test_default_instruction_mentions_tools(self):
        """기본 instruction은 도구 관련 언급"""
        # When
        agent = Agent(name="Test")

        # Then
        assert "tool" in agent.instruction.lower()

    def test_agent_with_different_models(self):
        """다양한 모델 지정 가능"""
        # Given / When
        agents = [
            Agent(name="Claude", model="anthropic/claude-sonnet-4-20250514"),
            Agent(name="GPT4", model="openai/gpt-4-turbo"),
            Agent(name="Gemini", model="google/gemini-pro"),
        ]

        # Then
        assert agents[0].model == "anthropic/claude-sonnet-4-20250514"
        assert agents[1].model == "openai/gpt-4-turbo"
        assert agents[2].model == "google/gemini-pro"

    def test_agent_repr(self):
        """Agent의 repr 확인"""
        # Given
        agent = Agent(name="TestAgent", model="test/model")

        # Then
        repr_str = repr(agent)
        assert "TestAgent" in repr_str
        assert "Agent" in repr_str
