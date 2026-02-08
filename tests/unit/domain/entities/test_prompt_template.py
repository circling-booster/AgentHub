"""PromptTemplate 엔티티 테스트

TDD로 작성됨:
- PromptArgument
- PromptTemplate
"""

from src.domain.entities.prompt_template import PromptArgument, PromptTemplate


class TestPromptArgument:
    def test_required_argument_creation(self):
        """필수 인자 생성"""
        arg = PromptArgument(name="name", required=True, description="User name")
        assert arg.name == "name"
        assert arg.required is True
        assert arg.description == "User name"

    def test_optional_argument_creation(self):
        """선택 인자 생성"""
        arg = PromptArgument(name="age", required=False)
        assert arg.required is False
        assert arg.description == ""


class TestPromptTemplate:
    def test_template_without_arguments(self):
        """인자 없는 템플릿 생성"""
        template = PromptTemplate(
            name="greeting",
            description="Simple greeting",
        )
        assert template.name == "greeting"
        assert template.arguments == []

    def test_template_with_arguments(self):
        """인자 있는 템플릿 생성"""
        args = [
            PromptArgument(name="name", required=True),
            PromptArgument(name="age", required=False),
        ]
        template = PromptTemplate(
            name="user_profile",
            description="User profile prompt",
            arguments=args,
        )
        assert len(template.arguments) == 2
        assert template.arguments[0].name == "name"
