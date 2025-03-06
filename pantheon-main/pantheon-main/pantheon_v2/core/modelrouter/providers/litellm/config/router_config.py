from typing import Dict, List, Optional
from pydantic import BaseModel
from enum import Enum

from pantheon_v2.settings.settings import Settings
from pantheon_v2.core.modelrouter.configs.global_llm_config import SupportedLLMModels
from pantheon_v2.core.modelrouter.configs.global_embedding_config import (
    SupportedEmbeddingsModels,
)


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    VERTEXAI = "vertexai"
    BEDROCK = "bedrock"


class LiteLLMProviderConfig(BaseModel):
    provider: Provider
    model_id: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    timeout: Optional[int] = None


class LiteLLMEmbeddingProviderConfig(BaseModel):
    provider: Provider
    model_id: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    dimensions: Optional[int] = None
    timeout: Optional[int] = None


class ModelProviderMapping:
    """Maps global model names to LiteLLM-specific configurations"""

    @classmethod
    def get_provider_configs(
        cls,
    ) -> Dict[SupportedLLMModels, List[LiteLLMProviderConfig]]:
        return {
            SupportedLLMModels.GPT_4O: [
                LiteLLMProviderConfig(
                    provider=Provider.OPENAI,
                    model_id="gpt-4o",
                    api_key=Settings.OPENAI_API_KEY,
                ),
            ],
            SupportedLLMModels.GPT_4O_MINI: [
                LiteLLMProviderConfig(
                    provider=Provider.OPENAI,
                    model_id="gpt-4o-mini",
                    api_key=Settings.OPENAI_API_KEY,
                )
            ],
            SupportedLLMModels.CLAUDE_3_5: [
                LiteLLMProviderConfig(
                    provider=Provider.ANTHROPIC,
                    model_id="claude-3-5-sonnet-20240620",
                    api_key=Settings.ANTHROPIC_API_KEY,
                )
            ],
            SupportedLLMModels.CLAUDE_3_7: [
                LiteLLMProviderConfig(
                    provider=Provider.ANTHROPIC,
                    model_id="claude-3-7-sonnet-20250219",
                    api_key=Settings.ANTHROPIC_API_KEY,
                )
            ],
            SupportedLLMModels.GPT_4: [
                LiteLLMProviderConfig(
                    provider=Provider.OPENAI,
                    model_id="gpt-4",
                    api_key=Settings.OPENAI_API_KEY,
                )
            ],
            SupportedLLMModels.GEMINI_FLASH_2: [
                LiteLLMProviderConfig(
                    provider=Provider.VERTEXAI,
                    model_id="vertex_ai/gemini-2.0-flash-exp",
                )
            ],
            SupportedLLMModels.BEDROCK_CLAUDE_3_5: [
                LiteLLMProviderConfig(
                    provider=Provider.BEDROCK,
                    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
                )
            ],
            SupportedLLMModels.GPT_O1: [
                LiteLLMProviderConfig(
                    provider=Provider.OPENAI,
                    model_id="o1",
                    api_key=Settings.OPENAI_API_KEY,
                    timeout=600,
                )
            ],
            SupportedLLMModels.GPT_O3_MINI: [
                LiteLLMProviderConfig(
                    provider=Provider.OPENAI,
                    model_id="o3-mini",
                    api_key=Settings.OPENAI_API_KEY,
                    timeout=600,
                )
            ],
            # SupportedLLMModels.BEDROCK_CLAUDE_3_7: [
            #     LiteLLMProviderConfig(
            #         provider=Provider.BEDROCK,
            #         model_id="anthropic.claude-3-7-sonnet-20240307-v1:0",
            #     )
            # ],
        }


class EmbeddingProviderMapping:
    """Maps global embedding model names to LiteLLM-specific configurations"""

    @classmethod
    def get_provider_configs(
        cls,
    ) -> Dict[SupportedEmbeddingsModels, List[LiteLLMEmbeddingProviderConfig]]:
        return {
            SupportedEmbeddingsModels.OPENAI_EMBEDDINGS: [
                LiteLLMEmbeddingProviderConfig(
                    provider=Provider.OPENAI,
                    model_id="text-embedding-3-large",
                    api_key=Settings.OPENAI_API_KEY,
                    dimensions=1536,  # Default dimension
                ),
            ],
        }
