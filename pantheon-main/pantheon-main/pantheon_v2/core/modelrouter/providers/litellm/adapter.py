from typing import List, Dict, Any, Union
from pantheon_v2.core.prompt.models import PromptMessage
from pantheon_v2.core.common.models import MessageType, ContentItem
from pantheon_v2.core.modelrouter.models.models import (
    EmbeddingResponse,
    EmbeddingData,
    Usage,
)
from pantheon_v2.core.modelrouter.providers.litellm.constants import (
    KEY_ROLE,
    KEY_CONTENT,
    KEY_TYPE,
    KEY_TEXT,
    KEY_IMAGE_URL,
    KEY_URL,
    LITE_LLM_CONTENT_TYPE_TEXT,
    LITE_LLM_CONTENT_TYPE_IMAGE_URL,
)
from pantheon_v2.core.modelrouter.providers.litellm.config.router_config import (
    Provider,
    ModelProviderMapping,
    LiteLLMProviderConfig,
)
from pantheon_v2.core.modelrouter.base_adapter import BaseAdapter
import structlog

logger = structlog.get_logger(__name__)


class LiteLLMAdapter(BaseAdapter):
    """Adapter to convert standard messages to LiteLLM format and handle responses"""

    def __init__(self):
        self.provider_configs = ModelProviderMapping.get_provider_configs()

    def format_content_items(
        self, content_items: List[ContentItem], model_name: str
    ) -> Union[str, List[Dict]]:
        """Format content items for LiteLLM"""
        formatted_content = []
        has_images = False

        # Get provider configs for the model
        provider_configs: List[LiteLLMProviderConfig] = self.provider_configs.get(
            model_name, []
        )
        needs_nested_image_url = any(
            config.provider == Provider.OPENAI  # Direct comparison with enum
            for config in provider_configs
        )

        for item in content_items:
            if item.type == MessageType.TEXT:
                formatted_content.append(
                    {KEY_TYPE: LITE_LLM_CONTENT_TYPE_TEXT, KEY_TEXT: item.text}
                )
            elif item.type == MessageType.IMAGE_URL:
                has_images = True
                if needs_nested_image_url:
                    formatted_content.append(
                        {
                            KEY_TYPE: LITE_LLM_CONTENT_TYPE_IMAGE_URL,
                            KEY_IMAGE_URL: {KEY_URL: item.image_url},
                        }
                    )
                else:
                    formatted_content.append(
                        {
                            KEY_TYPE: LITE_LLM_CONTENT_TYPE_IMAGE_URL,
                            KEY_IMAGE_URL: item.image_url,
                        }
                    )

        # If there are no images, return just the text content as a string
        if not has_images:
            return " ".join(item[KEY_TEXT] for item in formatted_content)

        return formatted_content

    def to_provider_format(
        self, messages: List[PromptMessage], model_name: str
    ) -> List[Dict[str, Any]]:
        """Convert standard messages to LiteLLM format"""
        litellm_messages = []

        for msg in messages:
            content = (
                msg.content
                if isinstance(msg.content, str)
                else self.format_content_items(msg.content, model_name)
            )

            litellm_messages.append({KEY_ROLE: msg.role, KEY_CONTENT: content})

        return litellm_messages

    def from_embedding_response(
        self, response: Any, model_name: str
    ) -> EmbeddingResponse:
        """Convert LiteLLM embedding response to standard EmbeddingResponse"""
        # Handle both object and dictionary responses
        if hasattr(response, "to_dict"):
            response_dict = response.to_dict()
        elif isinstance(response, dict):
            response_dict = response
        else:
            # Try to access as object properties
            response_dict = {
                "data": response.data if hasattr(response, "data") else [],
                "model": response.model if hasattr(response, "model") else model_name,
                "usage": response.usage.to_dict()
                if hasattr(response, "usage")
                else {"prompt_tokens": 0, "total_tokens": 0},
            }

        # Extract the data field
        data_items = response_dict.get("data", [])

        # Create embedding data objects
        embedding_data = []
        for item in data_items:
            # Handle the item being a dict or object
            if isinstance(item, dict):
                embedding = item.get("embedding", [])
                index = item.get("index")
            else:
                embedding = item.embedding if hasattr(item, "embedding") else []
                index = item.index if hasattr(item, "index") else None

            embedding_data.append(
                EmbeddingData(embedding=embedding, index=index, object="embedding")
            )

        # Extract usage information
        usage_info = response_dict.get("usage", {})
        if isinstance(usage_info, dict):
            prompt_tokens = usage_info.get("prompt_tokens", 0)
            total_tokens = usage_info.get("total_tokens", 0)
        else:
            prompt_tokens = (
                usage_info.prompt_tokens if hasattr(usage_info, "prompt_tokens") else 0
            )
            total_tokens = (
                usage_info.total_tokens if hasattr(usage_info, "total_tokens") else 0
            )

        return EmbeddingResponse(
            data=embedding_data,
            model=response_dict.get("model", model_name),
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=0,  # No completion tokens for embeddings
                total_tokens=total_tokens,
            ),
            raw_response=response,
        )
