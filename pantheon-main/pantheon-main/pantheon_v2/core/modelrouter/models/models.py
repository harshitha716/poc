from typing import Union, Optional, Any, Dict, List
from pantheon_v2.core.modelrouter.constants.constants import (
    SupportedLLMModels,
    SupportedEmbeddingsModels,
)
from pantheon_v2.core.prompt.chain import PromptChain
from enum import Enum
import base64

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ModelCapabilities(BaseModel):
    max_tokens: Optional[int] = None
    context_length: int
    supports_functions: bool = False
    max_completion_tokens: Optional[int] = None


class GlobalModelConfig(BaseModel):
    """Global model configuration independent of any provider"""

    capabilities: ModelCapabilities
    description: Optional[str] = None


class Message(BaseModel):
    """Single message in a conversation"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    prompt: PromptChain


class Usage(BaseModel):
    """Token usage information"""

    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class ModelResponse(BaseModel):
    """Standardized response format for model outputs"""

    content: str
    raw_response: Any
    parsed_response: Optional[Union[Dict[str, Any], BaseModel]] = Field(default=None)
    usage: Usage
    model: str


class GenerationRequest(BaseModel):
    """Request model for LLM generation"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    prompt_chain: PromptChain
    model_name: SupportedLLMModels
    temperature: Optional[float] = Field(
        default=None, description="Sampling temperature for generation"
    )
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens to generate"
    )

    def validate_prompt_chain(self) -> None:
        """Ensure prompt chain is valid"""
        if not self.prompt_chain.prompts:
            raise ValueError("Prompt chain cannot be empty")


class InputType(str, Enum):
    """Types of input for embeddings"""

    TEXT = "text"
    IMAGE = "image"


class ImageInput(BaseModel):
    """Image input for embedding generation"""

    base64_data: str  # Base64 encoded image data

    @field_validator("base64_data")
    @classmethod
    def validate_base64(cls, v):
        # Basic validation to check if it looks like base64
        try:
            # Try to decode a small portion to verify it's valid base64
            base64.b64decode(v[:20] + "=" * (4 - len(v[:20]) % 4))
        except Exception:
            raise ValueError("Invalid base64 encoding")
        return v


class EmbeddingInput(BaseModel):
    """Input for embedding generation"""

    type: InputType = InputType.TEXT
    content: Union[str, List[str], ImageInput]

    @field_validator("content")
    @classmethod
    def validate_content(cls, v, info):
        input_type = info.data.get("type")

        if input_type == InputType.TEXT and not isinstance(v, (str, list)):
            raise ValueError(
                "Content must be a string or list of strings for text embeddings"
            )

        if input_type == InputType.IMAGE and not isinstance(v, ImageInput):
            raise ValueError("Content must be an ImageInput for image embeddings")

        return v


class EmbeddingRequest(BaseModel):
    """Request for generating embeddings"""

    model_name: SupportedEmbeddingsModels
    input: EmbeddingInput
    dimensions: Optional[int] = None

    def validate_input(self) -> None:
        """Validate the embedding input"""
        if self.input.type == InputType.TEXT and not self.input.content:
            raise ValueError("Content cannot be empty for text embeddings")
        elif self.input.type == InputType.IMAGE and not isinstance(
            self.input.content, ImageInput
        ):
            raise ValueError("Content must be an ImageInput for image embeddings")


class EmbeddingData(BaseModel):
    """Embedding vector data"""

    embedding: List[float]
    index: Optional[int] = None
    object: str = "embedding"


class EmbeddingResponse(BaseModel):
    """Standardized response format for embedding outputs"""

    data: List[EmbeddingData]
    model: str
    usage: Usage
    raw_response: Any

    @property
    def embeddings(self) -> Union[List[float], List[List[float]]]:
        """Convenience accessor for the embedding vectors"""
        if len(self.data) == 1:
            return self.data[0].embedding
        return [item.embedding for item in self.data]


class EmbeddingCapabilities(BaseModel):
    """Capabilities of an embedding model"""

    dimensions: int
    max_input_length: int
    supports_batching: bool = True


class GlobalEmbeddingConfig(BaseModel):
    """Global configuration for an embedding model"""

    capabilities: EmbeddingCapabilities
    description: str
