import base64

from abc import ABC
from typing import List
from pantheon_v2.core.prompt.models import PromptConfig
from pantheon_v2.core.common.models import (
    MessageType,
    ContentItem,
    TextContent,
    ImageUrlContent,
)
from pantheon_v2.core.prompt.models import PromptMessage
from pydantic import BaseModel
from pantheon_v2.utils.file_utils import infer_file_type
from pantheon_v2.utils.file_utils import MIME_TYPE_TEXT
from pantheon_v2.core.common.models import MessageRole

from structlog import get_logger

logger = get_logger(__name__)


class BasePrompt(ABC, BaseModel):
    """Base class for all prompts in the system"""

    config: PromptConfig
    content_items: List[ContentItem] = []
    _template: str = ""  # Private template storage

    @property
    def template(self) -> str:
        """Get the processed template"""
        if not self._template:
            self._template = self._process_template()
        return self._template

    @template.setter
    def template(self, value: str):
        """Set the template value"""
        self._template = value

    @property
    def role(self) -> MessageRole:
        return self.config.role

    def _load_template(self, template: str) -> str:
        """Load template from string or file"""
        if template.endswith(".txt"):
            try:
                with open(template, "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                raise FileNotFoundError(f"Template file not found: {template}")
        elif "." in template:  # Check if there's any file extension
            raise ValueError(
                f"Only .txt files are supported for templates. Got: {template}"
            )

        return template

    def _process_template(self) -> str:
        """Process the template with variables."""
        processed = self._load_template(self.config.template)

        # Replace variables if provided
        if self.config.variables:
            for key, value in self.config.variables.items():
                processed = processed.replace(f"{{{{{key}}}}}", str(value))

        return processed

    def add_text(self, text: str) -> "BasePrompt":
        """Add text content to the prompt"""
        self.content_items.append(TextContent(type=MessageType.TEXT, text=text))
        return self

    def add_file(
        self,
        base64_content: str,
    ) -> "BasePrompt":
        """
        Add a base64 encoded file to the prompt content.
        Currently supports images (PNG, JPEG, JPG, GIF, WEBP) and PDFs.
        All files are added as ImageUrlContent with appropriate data URLs.

        Args:
            base64_content: Base64 encoded file content
            mime_type: MIME type from SupportedMimeTypes enum

        Returns:
            self for method chaining

        Raises:
            ValueError: If base64 content is invalid
        """
        try:
            base64.b64decode(base64_content)
        except Exception as e:
            raise ValueError(f"Invalid base64 content: {str(e)}")

        mime_type = infer_file_type(base64_content)
        if mime_type == MIME_TYPE_TEXT:
            raise ValueError(
                "File type is text, not supported. Please use add_text instead."
            )

        data_url = f"data:{mime_type};base64,{base64_content}"
        self.content_items.append(
            ImageUrlContent(type=MessageType.IMAGE_URL, image_url=data_url)
        )
        return self

    def build_messages(self) -> List[PromptMessage]:
        """Default implementation to build messages in standard format"""
        # Process template to handle variables
        processed_template = self.template

        # Create a new list starting with the template content
        all_content = [TextContent(type=MessageType.TEXT, text=processed_template)]

        # Add any additional content items
        all_content.extend(self.content_items)

        message = PromptMessage(role=self.role, content=all_content)

        return [message]
