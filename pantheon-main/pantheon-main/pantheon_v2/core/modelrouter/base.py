from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel
from pantheon_v2.core.modelrouter.models.models import (
    ModelResponse,
    GenerationRequest,
    EmbeddingRequest,
    EmbeddingResponse,
)
from pantheon_v2.core.modelrouter.configs.global_llm_config import (
    SUPPORTED_MODELS,
)


class RouterOptions(BaseModel):
    """Optional parameters for router initialization"""

    pass


class BaseModelRouter(ABC):
    """Abstract base class for model router implementations"""

    def __init__(self, options: Optional[RouterOptions] = None):
        self.options = options or RouterOptions()
        self.supported_models: set[str] = set(SUPPORTED_MODELS.get_config().keys())

    @abstractmethod
    async def generate(
        self,
        request: GenerationRequest,
    ) -> ModelResponse:
        """Generate a completion for the given messages."""
        pass

    @abstractmethod
    async def generate_embeddings(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResponse:
        """Generate embeddings for the given text."""
        pass
