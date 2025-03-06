from pantheon_v2.core.modelrouter.base import BaseModelRouter
from pantheon_v2.core.modelrouter.models.models import (
    ModelResponse,
    GenerationRequest,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingData,
    Usage,
)


class MockModelRouter(BaseModelRouter):
    """Concrete implementation of BaseModelRouter for testing"""

    async def generate(
        self,
        request: GenerationRequest,
    ) -> ModelResponse:
        # Simple implementation for testing
        return ModelResponse(
            content="test response",
            model=request.model_name.value,
            raw_response={"response": "test"},
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            parsed_response=None,
        )

    async def generate_embeddings(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResponse:
        # Simple implementation for testing embeddings
        return EmbeddingResponse(
            data=[
                EmbeddingData(
                    embedding=[0.1, 0.2, 0.3, 0.4, 0.5], index=0, object="embedding"
                )
            ],
            model=request.model_name.value,
            usage=Usage(prompt_tokens=10, completion_tokens=0, total_tokens=10),
            raw_response={"response": "test embedding"},
        )
