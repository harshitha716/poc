from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
from pantheon_v2.core.prompt.models import PromptMessage
from pantheon_v2.core.common.models import ContentItem


class BaseAdapter(ABC):
    """Base class for all provider-specific message adapters"""

    @abstractmethod
    def format_content_items(
        self, content_items: List[ContentItem], model_name: str
    ) -> Union[str, List[Dict]]:
        """Format content items into provider-specific format"""
        pass

    @abstractmethod
    def to_provider_format(
        self, messages: List[PromptMessage], model_name: str
    ) -> List[Dict[str, Any]]:
        """Convert standard messages to provider-specific format"""
        pass
