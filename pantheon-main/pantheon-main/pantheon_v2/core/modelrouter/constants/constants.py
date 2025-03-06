from enum import Enum


class SupportedLLMModels(str, Enum):
    """Enum of supported models to ensure type safety"""

    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    CLAUDE_3_5 = "claude-3.5-sonnet"
    CLAUDE_3_7 = "claude-3.7-sonnet"
    GPT_4 = "gpt-4"
    GEMINI_FLASH_2 = "gemini-2.0-flash"
    BEDROCK_CLAUDE_3_5 = "bedrock-claude-3-5-sonnet"
    GPT_O1 = "gpt-o1"
    GPT_O3_MINI = "gpt-o3-mini"


class RouterProvider(str, Enum):
    LITELLM = "litellm"


class SupportedEmbeddingsModels(str, Enum):
    OPENAI_EMBEDDINGS = "openai-embeddings"
