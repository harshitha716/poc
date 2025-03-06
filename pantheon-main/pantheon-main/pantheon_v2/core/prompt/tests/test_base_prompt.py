import pytest
from pathlib import Path
import base64

from pantheon_v2.core.prompt.base import BasePrompt
from pantheon_v2.core.prompt.models import PromptConfig
from pantheon_v2.core.common.models import (
    MessageRole,
    MessageType,
    TextContent,
    ImageUrlContent,
)
from pantheon_v2.utils.file_utils import MIME_TYPE_SIGNATURES


class TestPrompt(BasePrompt):
    """Test implementation of abstract BasePrompt"""

    pass


@pytest.fixture
def mock_response_model():
    # This fixture can be removed as it's no longer needed
    pass


@pytest.fixture
def basic_config(tmp_path):
    return PromptConfig(template="Test template", role=MessageRole.USER)


@pytest.fixture
def config_with_variables(tmp_path):
    return PromptConfig(
        template="Hello {{name}}!", variables={"name": "World"}, role=MessageRole.USER
    )


@pytest.fixture
def prompt(basic_config):
    return TestPrompt(config=basic_config)


class TestBasePrompt:
    def test_initialization(self, basic_config):
        prompt = TestPrompt(config=basic_config)
        assert prompt.template == "Test template"
        assert prompt.role == MessageRole.USER
        assert prompt.content_items == []

    def test_initialization_with_file_template(self, tmp_path):
        template_file = tmp_path / "template.txt"
        template_file.write_text("File template content")

        config = PromptConfig(template=str(template_file), role=MessageRole.USER)

        prompt = TestPrompt(config=config)
        assert prompt.template == "File template content"

    def test_add_text(self, prompt):
        result = prompt.add_text("Hello")
        assert len(prompt.content_items) == 1
        assert isinstance(prompt.content_items[0], TextContent)
        assert prompt.content_items[0].text == "Hello"
        assert prompt.content_items[0].type == MessageType.TEXT
        assert result == prompt  # Test method chaining

    def test_add_file_image(self, prompt):
        # Create a PNG image with valid signature
        png_signature = b"\x89PNG\r\n\x1a\n"  # PNG file signature
        fake_image = png_signature + b"fake_image_data"
        # Add proper base64 padding
        image_content = base64.b64encode(fake_image).decode()

        # Test with just the base64 content first
        result = prompt.add_file(image_content)

        assert len(prompt.content_items) == 1
        assert isinstance(prompt.content_items[0], ImageUrlContent)
        # The ImageUrlContent should contain the full data URL
        expected_url = (
            f"data:{MIME_TYPE_SIGNATURES[b'\x89PNG\r\n']};base64,{image_content}"
        )
        assert prompt.content_items[0].image_url == expected_url
        assert result == prompt  # Test method chaining

    def test_add_file_invalid_base64(self, prompt):
        with pytest.raises(ValueError, match="Invalid base64 content"):
            prompt.add_file("@@invalid@@")

    def test_variable_replacement(self, config_with_variables):
        prompt = TestPrompt(config=config_with_variables)
        messages = prompt.build_messages()

        assert len(messages) == 1
        assert messages[0].content[0].text == "Hello World!"

    def test_build_messages_with_template_only(self, prompt):
        messages = prompt.build_messages()
        assert len(messages) == 1
        assert messages[0].role == MessageRole.USER
        assert isinstance(messages[0].content[0], TextContent)
        assert messages[0].content[0].text == "Test template"

    def test_build_messages_with_content_items(self, prompt):
        prompt.add_text("Additional content")
        messages = prompt.build_messages()

        assert len(messages) == 1
        assert (
            len(messages[0].content) == 2
        )  # Should have both template and additional content
        assert messages[0].content[0].text == "Test template"
        assert messages[0].content[1].text == "Additional content"

    def test_template_not_found(self):
        nonexistent_path = Path("nonexistent.txt")
        config = PromptConfig(template=str(nonexistent_path), role=MessageRole.USER)

        with pytest.raises(FileNotFoundError):
            prompt = TestPrompt(config=config)
            # Access template property to trigger file loading and check
            _ = prompt.template
