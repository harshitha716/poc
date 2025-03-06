from pydantic import BaseModel, Field
from typing import Union, Optional, Dict
from typing import List
from pantheon_v2.core.common.models import MessageRole, ContentItem


class PromptConfig(BaseModel):
    """Configuration for prompt initialization"""

    template: str = Field(..., required=True)
    variables: Optional[Dict[str, str]] = None
    role: MessageRole = MessageRole.USER


class PromptMessage(BaseModel):
    """Standard message format for all prompts"""

    role: MessageRole
    content: Union[str, List[ContentItem]]
