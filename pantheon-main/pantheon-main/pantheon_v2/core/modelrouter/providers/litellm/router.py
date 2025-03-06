from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import structlog
from litellm import Router
import litellm

from pantheon_v2.settings.settings import Settings
from pantheon_v2.core.modelrouter.base import BaseModelRouter
from pantheon_v2.core.modelrouter.models.models import (
    ModelResponse,
    GenerationRequest,
    EmbeddingRequest,
    EmbeddingResponse,
    InputType,
)
from pantheon_v2.core.modelrouter.configs.global_llm_config import SUPPORTED_MODELS
from pantheon_v2.core.modelrouter.providers.litellm.config.router_config import (
    ModelProviderMapping,
    EmbeddingProviderMapping,
)
from pantheon_v2.core.modelrouter.exceptions.exceptions import (
    GenerationError,
    MaxTokensExceededError,
    EmbeddingError,
)
from pantheon_v2.core.modelrouter.providers.litellm.adapter import LiteLLMAdapter
from pantheon_v2.utils.file_utils import infer_file_type
from pantheon_v2.utils.trace_utils import get_trace_id

logger = structlog.get_logger(__name__)


@dataclass
class LangfuseConfig:
    """Configuration for Langfuse integration"""

    host: str = Settings.LANGFUSE_HOST
    public_key: str = Settings.LANGFUSE_PUBLIC_KEY
    secret_key: str = Settings.LANGFUSE_SECRET_KEY


class LiteLLMRouter(BaseModelRouter):
    """
    LiteLLM implementation of the BaseModelRouter.
    Handles routing requests to various LLM providers using LiteLLM.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.adapter = LiteLLMAdapter()
        self.global_configs = SUPPORTED_MODELS.get_config()
        self.provider_configs = ModelProviderMapping.get_provider_configs()
        self.embedding_provider_configs = (
            EmbeddingProviderMapping.get_provider_configs()
        )
        self.router: Optional[Router] = None

        self._configure_langfuse()
        self._setup_router()

    def _configure_langfuse(self) -> None:
        """Configure Langfuse integration"""
        logger.info(
            "Langfuse is enabled for environment", environment=Settings.ENVIRONMENT
        )
        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]

    def _setup_router(self) -> None:
        """Initialize the LiteLLM router with model configurations"""
        litellm.drop_params = True
        model_list = [
            {
                "model_name": model_name,
                "litellm_params": {
                    "model": provider.model_id,
                    **{
                        k: v
                        for k, v in provider.model_dump().items()
                        if k not in ["provider", "model_id"]
                    },
                },
            }
            for model_name, providers in self.provider_configs.items()
            for provider in providers
        ]

        # Add embedding models
        embedding_models = [
            {
                "model_name": model_name.value,
                "litellm_params": {
                    "model": provider.model_id,
                    **{
                        k: v
                        for k, v in provider.model_dump().items()
                        if k not in ["provider", "model_id"]
                    },
                },
            }
            for model_name, providers in self.embedding_provider_configs.items()
            for provider in providers
        ]

        model_list.extend(embedding_models)
        self.router = Router(model_list=model_list)

    def _add_trace_id_to_metadata(
        self, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add the current trace ID to metadata as 'session_id' for Langfuse tracking.

        Args:
            metadata (Optional[Dict[str, Any]]): Existing metadata dictionary or None

        Returns:
            Dict[str, Any]: Metadata dictionary with trace ID added as session_id
        """
        if metadata is None:
            metadata = {}

        trace_id = get_trace_id()
        if trace_id:
            metadata["session_id"] = trace_id

        return metadata

    def _prepare_completion_params(
        self,
        messages: List[Dict[str, str]],
        model_name: str,
        temperature: Optional[float],
        max_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Prepare parameters for LiteLLM completion"""
        model_config = self.global_configs[model_name]
        model_max_tokens = model_config.capabilities.max_tokens

        if max_tokens is not None and max_tokens > model_max_tokens:
            raise MaxTokensExceededError(
                f"Requested max_tokens ({max_tokens}) exceeds model's capability ({model_max_tokens})"
            )

        params = {
            "messages": messages,
            "model": model_name,
            "max_tokens": max_tokens or model_max_tokens,
        }

        if temperature is not None:
            params["temperature"] = temperature

        return params

    async def generate(self, request: GenerationRequest) -> ModelResponse:
        """Generate a response using the specified model."""
        try:
            # Validate request
            request.validate_prompt_chain()

            # Get messages in standard format and convert to litellm format
            standard_messages = request.prompt_chain.build_messages()
            litellm_messages = self.adapter.to_provider_format(
                standard_messages, request.model_name.value
            )

            completion_params = self._prepare_completion_params(
                litellm_messages,
                request.model_name.value,
                request.temperature,
                request.max_tokens,
            )

            # Add trace ID to metadata for Langfuse
            completion_params["metadata"] = self._add_trace_id_to_metadata(
                completion_params.get("metadata")
            )

            response = await self.router.acompletion(**completion_params)
            content = response.choices[0].message.content

            # Use prompt chain to parse the response
            parsed_content = request.prompt_chain.parse_response(content)

            return ModelResponse(
                content=content,
                raw_response=response,
                parsed_response=parsed_content,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                model=request.model_name.value,
            )

        except Exception as e:
            raise GenerationError(f"Error generating response: {str(e)}") from e

    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings using the specified model."""
        try:
            # Validate request
            request.validate_input()

            # Find the provider config for the requested model
            provider_configs = self.embedding_provider_configs.get(
                request.model_name, []
            )
            if not provider_configs:
                raise EmbeddingError(
                    f"No provider configuration found for model: {request.model_name}"
                )

            # Use the first available provider
            provider_config = provider_configs[0]

            # Set dimensions if specified
            dimensions = request.dimensions or provider_config.dimensions

            embedding_params = {
                "model": request.model_name.value,
                "dimensions": dimensions if dimensions else None,
            }

            # Add trace ID to metadata for Langfuse
            embedding_params["metadata"] = self._add_trace_id_to_metadata(
                embedding_params.get("metadata")
            )

            # Prepare input based on type
            if request.input.type == InputType.TEXT:
                embedding_params["input"] = request.input.content
            elif request.input.type == InputType.IMAGE:
                # Use the existing utility function to infer the mime type
                image_input = request.input.content
                mime_type = infer_file_type(image_input.base64_data)

                # If it's not an image type or detection failed, default to jpeg
                if not mime_type.startswith("image/"):
                    raise EmbeddingError(f"Invalid image input: {mime_type}")

                # Format the base64 data with the appropriate prefix
                base64_with_prefix = (
                    f"data:{mime_type};base64,{image_input.base64_data}"
                )

                # LiteLLM expects image inputs in a specific format for embeddings
                embedding_params["input"] = base64_with_prefix

            # Call the LiteLLM embedding API
            response = await self.router.aembedding(**embedding_params)

            # Use the adapter to convert the response
            return self.adapter.from_embedding_response(
                response, request.model_name.value
            )

        except Exception as e:
            raise EmbeddingError(f"Error generating embeddings: {str(e)}") from e
