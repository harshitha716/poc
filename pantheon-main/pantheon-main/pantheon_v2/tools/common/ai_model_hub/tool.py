import structlog
from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.core.tool_registry import ToolRegistry
from pantheon_v2.tools.common.ai_model_hub.models import (
    AIModelHubToolGenerateLLMInput,
    AIModelHubToolGenerateLLMOutput,
    AIModelHubToolGenerateEmbeddingsInput,
    AIModelHubToolGenerateEmbeddingsOutput,
)
from pantheon_v2.core.modelrouter.factory import ModelRouterFactory
from pantheon_v2.core.modelrouter.constants.constants import RouterProvider
from pantheon_v2.core.modelrouter.models.models import (
    GenerationRequest,
    ModelResponse,
    EmbeddingRequest,
    EmbeddingInput,
)

logger = structlog.get_logger(__name__)


@ToolRegistry.register_tool(
    description="Tool for making calls to AI models including LLMs and embedding models"
)
class AIModelHubTool(BaseTool):
    def __init__(self):
        self.model_router = ModelRouterFactory.get_router(RouterProvider.LITELLM)

    async def initialize(self) -> None:
        """Initialize the AI Model tool"""
        try:
            logger.info("AI Model tool initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize AI Model tool", error=str(e))
            raise

    @ToolRegistry.register_tool_action(
        description="Call LLM models with a prompt chain to reason and generate a response"
    )
    async def generate(
        self, params: AIModelHubToolGenerateLLMInput
    ) -> AIModelHubToolGenerateLLMOutput:
        """Generate text using the specified LLM model."""
        try:
            # Create the generation request using the provided prompt chain
            request = GenerationRequest(
                prompt_chain=params.prompt_chain,
                model_name=params.model_name,
                temperature=params.temperature,
                max_tokens=params.max_tokens,
            )

            # Generate the response
            response: ModelResponse = await self.model_router.generate(request)

            return AIModelHubToolGenerateLLMOutput(
                content=response.content,
                raw_response=response.raw_response,
                parsed_response=response.parsed_response,
                usage=response.usage,
            )

        except Exception as e:
            logger.error("Error generating response", error=str(e))
            raise

    @ToolRegistry.register_tool_action(
        description="Generate embeddings from text or images using embedding models"
    )
    async def generate_embeddings(
        self, params: AIModelHubToolGenerateEmbeddingsInput
    ) -> AIModelHubToolGenerateEmbeddingsOutput:
        """Generate embeddings for the specified input using the specified embedding model."""
        try:
            # Create the embedding request
            request = EmbeddingRequest(
                model_name=params.model_name,
                input=EmbeddingInput(type=params.input_type, content=params.content),
            )

            # Generate the embeddings
            response = await self.model_router.generate_embeddings(request)

            logger.info(
                "Generated embeddings response",
                response_type=type(response).__name__,
                has_data=hasattr(response, "data"),
            )

            # Extract embeddings based on the EmbeddingResponse format
            # The EmbeddingResponse contains a 'data' field which is a list of EmbeddingData objects
            # Each EmbeddingData has an 'embedding' field which is the actual vector
            embeddings = []
            if hasattr(response, "data") and response.data:
                embeddings = [data.embedding for data in response.data]

            logger.info(
                "Extracted embeddings",
                embedding_count=len(embeddings),
                first_embedding_type=type(embeddings[0]).__name__
                if embeddings
                else None,
            )

            return AIModelHubToolGenerateEmbeddingsOutput(
                embeddings=embeddings,
                model=response.model,
                usage=response.usage,
            )

        except Exception as e:
            logger.error("Error generating embeddings", error=str(e), exc_info=True)
            raise
