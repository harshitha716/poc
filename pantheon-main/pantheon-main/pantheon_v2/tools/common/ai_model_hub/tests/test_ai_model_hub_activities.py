import pytest
from unittest.mock import AsyncMock, patch
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from pantheon_v2.tools.common.ai_model_hub.activities import (
    generate_llm_model_response,
    generate_embeddings,
)
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
    SupportedEmbeddingsModels,
)
from pantheon_v2.core.modelrouter.models.models import (
    Usage,
    ModelResponse,
    InputType,
)


class TestResponseModel(BaseModel):
    """Simple response model for testing"""

    result: Optional[str] = Field(None, description="Test result field")
    data: Optional[Dict[str, Any]] = Field(None, description="Test data field")


class TestLLMModelActivities:
    @pytest.fixture
    def mock_model_router_factory(self):
        """Mock the ModelRouterFactory to prevent actual API calls"""
        with patch(
            "pantheon_v2.core.modelrouter.factory.ModelRouterFactory"
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
    async def test_generate_llm_model_response(
        self, mock_model_router_factory, sample_prompt_chain
    ):
        """Test the generate_llm_model_response activity"""
        mock_factory, mock_router = mock_model_router_factory

        # Create mock output
        mock_response = ModelResponse(
            model="gpt-4",  # Add the required model field
            content="Generated content",
            raw_response={"choices": [{"text": "Generated content"}]},
            parsed_response={"result": "success"},
            usage=Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        )
        mock_router.generate.return_value = mock_response

        # Create mock LLMModelOutput
        mock_output = AIModelHubToolGenerateLLMOutput(
            content="Generated content",
            raw_response={"choices": [{"text": "Generated content"}]},
            parsed_response={"result": "success"},
            usage=Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        )

        # Create input parameters
        input_params = AIModelHubToolGenerateLLMInput(
            prompt_chain=sample_prompt_chain,
            model_name=SupportedLLMModels.GPT_4,
            temperature=0.7,
            max_tokens=100,
        )

        # Mock the LLMModelTool.generate method
        with patch(
            "pantheon_v2.tools.common.ai_model_hub.activities.AIModelHubTool"
        ) as MockTool:
            mock_tool_instance = MockTool.return_value
            mock_tool_instance.initialize = AsyncMock()
            mock_tool_instance.generate = AsyncMock(return_value=mock_output)

            # Call the activity
            result = await generate_llm_model_response(input_params)

            # Verify tool was initialized
            mock_tool_instance.initialize.assert_called_once()

            # Verify generate was called with correct parameters
            mock_tool_instance.generate.assert_called_once()
            call_args = mock_tool_instance.generate.call_args[0][0]
            assert call_args.prompt_chain == sample_prompt_chain
            assert call_args.model_name == SupportedLLMModels.GPT_4
            assert call_args.temperature == 0.7
            assert call_args.max_tokens == 100

            # Verify result
            assert result == mock_output
            assert result.content == "Generated content"
            assert result.parsed_response == {"result": "success"}
            assert result.usage.total_tokens == 30

    @pytest.mark.asyncio
    async def test_generate_llm_model_response_error(
        self, mock_model_router_factory, sample_prompt_chain
    ):
        """Test error handling in the generate_llm_model_response activity"""
        mock_factory, mock_router = mock_model_router_factory

        # Create input parameters
        input_params = AIModelHubToolGenerateLLMInput(
            prompt_chain=sample_prompt_chain,
            model_name=SupportedLLMModels.GPT_4,
            temperature=0.7,
            max_tokens=100,
        )

        # Mock the LLMModelTool.generate method to raise an exception
        with patch(
            "pantheon_v2.tools.common.ai_model_hub.activities.AIModelHubTool"
        ) as MockTool:
            mock_tool_instance = MockTool.return_value
            mock_tool_instance.initialize = AsyncMock()
            mock_tool_instance.generate = AsyncMock(side_effect=Exception("Test error"))

            # Call the activity and expect exception to be propagated
            with pytest.raises(Exception) as exc_info:
                await generate_llm_model_response(input_params)

            assert "Test error" in str(exc_info.value)


class TestEmbeddingsActivities:
    @pytest.fixture
    def mock_model_router_factory(self):
        """Mock the ModelRouterFactory to prevent actual API calls"""
        with patch(
            "pantheon_v2.core.modelrouter.factory.ModelRouterFactory"
        ) as mock_factory:
            mock_router = AsyncMock()
            mock_factory.get_router.return_value = mock_router
            yield mock_factory, mock_router

    @pytest.mark.asyncio
    async def test_generate_embeddings_activity(self, mock_model_router_factory):
        """Test the generate_embeddings activity"""
        mock_factory, mock_router = mock_model_router_factory

        # Create mock output
        mock_output = AIModelHubToolGenerateEmbeddingsOutput(
            embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            model="openai-embeddings",
            usage=Usage(prompt_tokens=8, completion_tokens=0, total_tokens=8),
        )

        # Create input parameters
        input_params = AIModelHubToolGenerateEmbeddingsInput(
            model_name=SupportedEmbeddingsModels.OPENAI_EMBEDDINGS,
            input_type=InputType.TEXT,
            content="Test text for embedding",
        )

        # Mock the AIModelHubTool.generate_embeddings method
        with patch(
            "pantheon_v2.tools.common.ai_model_hub.activities.AIModelHubTool"
        ) as MockTool:
            mock_tool_instance = MockTool.return_value
            mock_tool_instance.initialize = AsyncMock()
            mock_tool_instance.generate_embeddings = AsyncMock(return_value=mock_output)

            # Call the activity
            result = await generate_embeddings(input_params)

            # Verify tool was initialized
            mock_tool_instance.initialize.assert_called_once()

            # Verify generate_embeddings was called with correct parameters
            mock_tool_instance.generate_embeddings.assert_called_once()
            call_args = mock_tool_instance.generate_embeddings.call_args[0][0]
            assert call_args.model_name == SupportedEmbeddingsModels.OPENAI_EMBEDDINGS
            assert call_args.input_type == InputType.TEXT
            assert call_args.content == "Test text for embedding"

            # Verify result
            assert result == mock_output
            assert len(result.embeddings) == 2
            assert result.model == "openai-embeddings"
            assert result.usage.prompt_tokens == 8
            assert result.usage.total_tokens == 8

    @pytest.mark.asyncio
    async def test_generate_embeddings_activity_error(self, mock_model_router_factory):
        """Test error handling in the generate_embeddings activity"""
        mock_factory, mock_router = mock_model_router_factory

        # Create input parameters
        input_params = AIModelHubToolGenerateEmbeddingsInput(
            model_name=SupportedEmbeddingsModels.OPENAI_EMBEDDINGS,
            input_type=InputType.TEXT,
            content="Test text for embedding",
        )

        # Mock the AIModelHubTool.generate_embeddings method to raise an exception
        with patch(
            "pantheon_v2.tools.common.ai_model_hub.activities.AIModelHubTool"
        ) as MockTool:
            mock_tool_instance = MockTool.return_value
            mock_tool_instance.initialize = AsyncMock()
            mock_tool_instance.generate_embeddings = AsyncMock(
                side_effect=Exception("Embedding error")
            )

            # Call the activity and expect exception to be propagated
            with pytest.raises(Exception) as exc_info:
                await generate_embeddings(input_params)

            assert "Embedding error" in str(exc_info.value)
