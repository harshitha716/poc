import pytest
from pantheon_v2.core.prompt.generic import GenericPrompt
from pantheon_v2.core.prompt.models import PromptConfig
from pantheon_v2.core.common.models import MessageRole


@pytest.fixture
def basic_config():
    return PromptConfig(template="Test template", role=MessageRole.USER)


class TestGenericPrompt:
    def test_initialization(self, basic_config):
        prompt = GenericPrompt(config=basic_config)
        assert prompt.template == "Test template"
        assert prompt.role == MessageRole.USER
        assert prompt.content_items == []

    def test_with_variables(self):
        config = PromptConfig(
            template="Hello {{name}}!",
            variables={"name": "World"},
            role=MessageRole.USER,
        )

        prompt = GenericPrompt(config=config)
        messages = prompt.build_messages()

        assert len(messages) == 1
        assert messages[0].content[0].text == "Hello World!"

    def test_add_content(self, basic_config):
        prompt = GenericPrompt(config=basic_config)
        prompt.add_text("Additional content")

        messages = prompt.build_messages()
        assert len(messages) == 1
        assert (
            len(messages[0].content) == 2
        )  # Should have both template and additional content
        assert messages[0].content[0].text == "Test template"
        assert messages[0].content[1].text == "Additional content"
