from pydantic import BaseModel, Field
from typing import Optional, Any, List
from pantheon_v2.core.modelrouter.constants.constants import (
    SupportedLLMModels,
    SupportedEmbeddingsModels,
)
from pantheon_v2.core.prompt.chain import PromptChain
from pantheon_v2.core.modelrouter.models.models import Usage, InputType


class AIModelHubToolGenerateLLMInput(BaseModel):
    prompt_chain: PromptChain = Field(description="Prompt chain to send to the model")
    model_name: SupportedLLMModels = Field(description="Name of the LLM model to use")
    temperature: Optional[float] = Field(
        default=None, description="Temperature for generation"
    )
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens to generate"
    )

    class Config:
        arbitrary_types_allowed = True


class AIModelHubToolGenerateLLMOutput(BaseModel):
    content: str = Field(description="Generated content from the model")
    raw_response: Any = Field(description="Raw response from the model")
    parsed_response: Optional[Any] = Field(description="Parsed response if available")
    usage: Usage = Field(description="Token usage statistics")

    class Config:
        arbitrary_types_allowed = True


class AIModelHubToolGenerateEmbeddingsInput(BaseModel):
    model_name: SupportedEmbeddingsModels = Field(
        description="Name of the embedding model to use"
    )
    input_type: InputType = Field(
        default=InputType.TEXT, description="Type of input to embed (text or image)"
    )
    content: str = Field(description="Text content or base64 encoded image to embed")

    class Config:
        arbitrary_types_allowed = True


class AIModelHubToolGenerateEmbeddingsOutput(BaseModel):
    embeddings: List[List[float]] = Field(description="List of embedding vectors")
    model: str = Field(description="Model used for embeddings")
    usage: Usage = Field(description="Token usage statistics")

    class Config:
        arbitrary_types_allowed = True
