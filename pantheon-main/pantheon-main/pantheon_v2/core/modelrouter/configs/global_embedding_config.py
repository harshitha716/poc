from typing import Dict
from pantheon_v2.core.modelrouter.constants.constants import SupportedEmbeddingsModels
from pantheon_v2.core.modelrouter.models.models import (
    EmbeddingCapabilities,
    GlobalEmbeddingConfig,
)


class SUPPORTED_EMBEDDING_MODELS:
    """Global embedding model configurations"""

    @classmethod
    def get_config(cls) -> Dict[SupportedEmbeddingsModels, GlobalEmbeddingConfig]:
        return {
            SupportedEmbeddingsModels.OPENAI_EMBEDDINGS: GlobalEmbeddingConfig(
                capabilities=EmbeddingCapabilities(
                    dimensions=1536,
                    max_input_length=8191,  # Maximum tokens for OpenAI embeddings
                    supports_batching=True,
                ),
                description="OpenAI text-embedding-3-large model for high-quality embeddings",
            ),
        }
