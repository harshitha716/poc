import pytest
from unittest.mock import AsyncMock, patch
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from pantheon_v2.tools.common.ai_model_hub.tool import AIModelHubTool
from pantheon_v2.tools.common.ai_model_hub.models import (
    AIModelHubToolGenerateLLMInput,
    AIModelHubToolGenerateLLMOutput,
    AIModelHubToolGenerateEmbeddingsInput,
    AIModelHubToolGenerateEmbeddingsOutput,
)
from pantheon_v2.core.prompt.chain import PromptChain, ChainConfig
from pantheon_v2.core.prompt.generic import GenericPrompt
from pantheon_v2.core.prompt.models import PromptConfig
from pantheon_v2.core.common.models import MessageRole
from pantheon_v2.core.modelrouter.constants.constants import (
    SupportedLLMModels,
    RouterProvider,
    SupportedEmbeddingsModels,
)
from pantheon_v2.core.modelrouter.models.models import (
    GenerationRequest,
    ModelResponse,
    Usage,
    InputType,
)


class TestResponseModel(BaseModel):
    """Simple response model for testing"""

    result: Optional[str] = Field(None, description="Test result field")
    data: Optional[Dict[str, Any]] = Field(None, description="Test data field")


class TestAIModelHubTool:
    @pytest.fixture
    def mock_model_router_factory(self):
        """Mock the ModelRouterFactory to prevent actual API calls"""
        with patch(
            "pantheon_v2.tools.common.ai_model_hub.tool.ModelRouterFactory"
        ) as mock_factory:
            mock_router = AsyncMock()
            mock_factory.get_router.return_value = mock_router
            yield mock_factory, mock_router

    @pytest.fixture
    def sample_prompt_chain(self):
        prompt = GenericPrompt(
            config=PromptConfig(
                template="Test prompt",
                role=MessageRole.USER,
            )
        )
        chain = PromptChain(config=ChainConfig(response_model=TestResponseModel))
        chain.add_prompt(prompt)
        return chain

    @pytest.mark.asyncio
    async def test_initialize(self, mock_model_router_factory):
        """Test tool initialization"""
        mock_factory, mock_router = mock_model_router_factory

        tool = AIModelHubTool()
        await tool.initialize()

        # Verify the router was created with the correct provider
        mock_factory.get_router.assert_called_once_with(RouterProvider.LITELLM)

    @pytest.mark.asyncio
    async def test_generate_success(
        self, mock_model_router_factory, sample_prompt_chain
    ):
        """Test successful generation"""
        mock_factory, mock_router = mock_model_router_factory

        # Mock response
        mock_response = ModelResponse(
            model="gpt-4",  # Add the required model field
            content="Generated text",
            raw_response={"choices": [{"text": "Generated text"}]},
            parsed_response={"result": "success"},
            usage=Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        )
        mock_router.generate.return_value = mock_response

        # Create tool
        tool = AIModelHubTool()

        # Test input
        input_params = AIModelHubToolGenerateLLMInput(
            prompt_chain=sample_prompt_chain,
            model_name=SupportedLLMModels.GPT_4,
            temperature=0.7,
            max_tokens=100,
        )

        # Execute
        result = await tool.generate(input_params)

        # Verify
        assert isinstance(result, AIModelHubToolGenerateLLMOutput)
        assert result.content == "Generated text"
        assert result.raw_response == {"choices": [{"text": "Generated text"}]}
        assert result.parsed_response == {"result": "success"}
        assert result.usage.prompt_tokens == 10
        assert result.usage.completion_tokens == 20
        assert result.usage.total_tokens == 30

        # Verify correct request was sent
        mock_router.generate.assert_called_once()
        call_args = mock_router.generate.call_args[0][0]
        assert isinstance(call_args, GenerationRequest)
        assert call_args.prompt_chain == sample_prompt_chain
        assert call_args.model_name == SupportedLLMModels.GPT_4
        assert call_args.temperature == 0.7
        assert call_args.max_tokens == 100

    @pytest.mark.asyncio
    async def test_generate_error(self, mock_model_router_factory, sample_prompt_chain):
        """Test error handling during generation"""
        mock_factory, mock_router = mock_model_router_factory

        # Mock error
        mock_router.generate.side_effect = Exception("Model error")

        # Create tool
        tool = AIModelHubTool()

        # Test input
        input_params = AIModelHubToolGenerateLLMInput(
            prompt_chain=sample_prompt_chain,
            model_name=SupportedLLMModels.GPT_4,
            temperature=0.7,
            max_tokens=100,
        )

        # Execute and verify exception is raised
        with pytest.raises(Exception) as exc_info:
            await tool.generate(input_params)

        # Update the assertion to match the actual error message
        assert str(exc_info.value) == "Model error"

    @pytest.mark.asyncio
    async def test_generate_with_default_values(
        self, mock_model_router_factory, sample_prompt_chain
    ):
        """Test generation with default parameter values"""
        mock_factory, mock_router = mock_model_router_factory

        # Mock response
        mock_response = ModelResponse(
            model="gpt-4",  # Add the required model field
            content="Generated text",
            raw_response={"choices": [{"text": "Generated text"}]},
            parsed_response=None,  # Test with None parsed_response
            usage=Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        )
        mock_router.generate.return_value = mock_response

        # Create tool
        tool = AIModelHubTool()

        # Test input with explicit None values for optional parameters
        input_params = AIModelHubToolGenerateLLMInput(
            prompt_chain=sample_prompt_chain,
            model_name=SupportedLLMModels.GPT_4,
            temperature=None,  # Explicitly set to None
            max_tokens=None,  # Explicitly set to None
        )

        # Execute
        result = await tool.generate(input_params)

        # Verify
        assert isinstance(result, AIModelHubToolGenerateLLMOutput)
        assert result.content == "Generated text"
        assert result.parsed_response is None

        # Verify request was sent with None values for optional params
        call_args = mock_router.generate.call_args[0][0]
        assert call_args.temperature is None
        assert call_args.max_tokens is None

    @pytest.mark.asyncio
    async def test_generate_embeddings_success(self, mock_model_router_factory):
        """Test successful embeddings generation"""
        mock_factory, mock_router = mock_model_router_factory

        # Mock response
        mock_embedding_data = [
            type("EmbeddingData", (), {"embedding": [0.1, 0.2, 0.3, 0.4]})(),
            type("EmbeddingData", (), {"embedding": [0.5, 0.6, 0.7, 0.8]})(),
        ]
        mock_response = type(
            "EmbeddingResponse",
            (),
            {
                "data": mock_embedding_data,
                "model": "openai-embeddings",
                "usage": Usage(prompt_tokens=8, completion_tokens=0, total_tokens=8),
            },
        )()
        mock_router.generate_embeddings.return_value = mock_response

        # Create tool
        tool = AIModelHubTool()

        # Test input
        input_params = AIModelHubToolGenerateEmbeddingsInput(
            model_name=SupportedEmbeddingsModels.OPENAI_EMBEDDINGS,
            input_type=InputType.TEXT,
            content="Test text for embedding",
        )

        # Execute
        result = await tool.generate_embeddings(input_params)

        # Verify
        assert isinstance(result, AIModelHubToolGenerateEmbeddingsOutput)
        assert len(result.embeddings) == 2
        assert result.embeddings[0] == [0.1, 0.2, 0.3, 0.4]
        assert result.embeddings[1] == [0.5, 0.6, 0.7, 0.8]
        assert result.model == "openai-embeddings"
        assert result.usage.prompt_tokens == 8
        assert result.usage.total_tokens == 8

        # Verify correct request was sent
        mock_router.generate_embeddings.assert_called_once()
        call_args = mock_router.generate_embeddings.call_args[0][0]
        assert call_args.model_name == SupportedEmbeddingsModels.OPENAI_EMBEDDINGS
        assert call_args.input.type == InputType.TEXT
        assert call_args.input.content == "Test text for embedding"

    @pytest.mark.asyncio
    async def test_generate_embeddings_error(self, mock_model_router_factory):
        """Test error handling during embeddings generation"""
        mock_factory, mock_router = mock_model_router_factory

        # Mock error
        mock_router.generate_embeddings.side_effect = Exception("Embedding model error")

        # Create tool
        tool = AIModelHubTool()

        # Test input
        input_params = AIModelHubToolGenerateEmbeddingsInput(
            model_name=SupportedEmbeddingsModels.OPENAI_EMBEDDINGS,
            input_type=InputType.TEXT,
            content="Test text for embedding",
        )

        # Execute and verify exception is raised
        with pytest.raises(Exception) as exc_info:
            await tool.generate_embeddings(input_params)

        assert str(exc_info.value) == "Embedding model error"
