from enum import Enum
from typing import Union, Dict
from pydantic import BaseModel


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE_URL = "image_url"
    FUNCTION_CALL = "function_call"


class ContentItem(BaseModel):
    """Base class for different types of content"""

    type: MessageType


class TextContent(ContentItem):
    """Text content type"""

    type: MessageType = MessageType.TEXT
    text: str


class ImageUrlContent(ContentItem):
    """Image URL content type"""

    type: MessageType = MessageType.IMAGE_URL
    image_url: Union[str, Dict[str, str]]
