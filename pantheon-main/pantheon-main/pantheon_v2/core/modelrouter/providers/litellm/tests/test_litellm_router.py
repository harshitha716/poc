import pytest
from unittest.mock import Mock, patch, AsyncMock, PropertyMock
from pydantic import BaseModel

from pantheon_v2.core.modelrouter.providers.litellm.router import LiteLLMRouter
from pantheon_v2.core.modelrouter.models.models import (
    GenerationRequest,
    PromptChain,
    EmbeddingRequest,
    EmbeddingInput,
    EmbeddingResponse,
    EmbeddingData,
    Usage,
    InputType,
    ImageInput,
)
from pantheon_v2.core.common.models import MessageRole, TextContent, MessageType
from pantheon_v2.core.modelrouter.constants.constants import (
    SupportedLLMModels,
    SupportedEmbeddingsModels,
)
from pantheon_v2.core.modelrouter.exceptions.exceptions import (
    GenerationError,
    EmbeddingError,
)
from pantheon_v2.settings.settings import Settings
from pantheon_v2.core.prompt.models import PromptMessage, PromptConfig
from pantheon_v2.core.prompt.generic import GenericPrompt


@pytest.fixture
def mock_litellm_response():
    return Mock(
        choices=[Mock(message=Mock(content="Test response"))],
        usage=Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )


@pytest.fixture
def mock_settings():
    settings = Mock(spec=Settings)
    settings.llm = Mock()
    settings.llm.api_keys = {"openai": "test-key"}
    settings.llm.model_provider_mapping = {
        "gpt-4": {"provider": "openai", "model": "gpt-4"}
    }
    return settings


@pytest.fixture
def mock_message_prompt():
    prompt = Mock(spec=PromptChain)
    prompt.build_messages.return_value = ["Test message"]
    return prompt


@pytest.fixture
def router(mock_settings):
    mock_router = Mock()
    mock_router.acompletion = AsyncMock()

    with patch("litellm.Router", return_value=mock_router), patch(
        "pantheon_v2.core.modelrouter.providers.litellm.router.LiteLLMRouter._setup_router"
    ):
        router = LiteLLMRouter(settings=mock_settings)
        router.router = mock_router
        return router


@pytest.fixture
def mock_prompt_chain():
    """Create a mock prompt chain with proper structure"""
    chain = Mock(spec=PromptChain)

    # Create a proper prompt message
    message = PromptMessage(
        role=MessageRole.USER,
        content=[TextContent(type=MessageType.TEXT, text="Test message")],
    )

    # Mock the prompts property
    type(chain).prompts = PropertyMock(
        return_value=[
            GenericPrompt(
                config=PromptConfig(template="Test template", role=MessageRole.USER)
            )
        ]
    )

    # Mock build_messages to return our properly structured message
    chain.build_messages.return_value = [message]

    # Mock parse_response
    chain.parse_response.return_value = {"response": "Test response"}

    return chain


@pytest.mark.asyncio
async def test_initialization(mock_settings):
    """Test router initialization and configuration"""
    with patch("litellm.Router"), patch(
        "pantheon_v2.core.modelrouter.providers.litellm.router.LiteLLMRouter._setup_router"
    ):
        router = LiteLLMRouter(settings=mock_settings)
        assert isinstance(router, LiteLLMRouter)
        assert hasattr(router, "router")


@pytest.mark.asyncio
async def test_generate(router, mock_litellm_response, mock_prompt_chain):
    """Test generation with prompt chain"""
    mock_litellm_response.choices[0].message.content = '{"response": "Test response"}'
    router.router.acompletion.return_value = mock_litellm_response

    request = GenerationRequest(
        prompt_chain=mock_prompt_chain,
        model_name=SupportedLLMModels.GPT_4O,
        temperature=0.7,
    )

    response = await router.generate(request)

    assert response.content == '{"response": "Test response"}'
    assert response.parsed_response == {"response": "Test response"}
    assert response.usage.prompt_tokens == 10
    assert response.usage.completion_tokens == 5
    assert response.usage.total_tokens == 15
    assert response.model == SupportedLLMModels.GPT_4O.value

    # Verify the router was called with correct parameters
    router.router.acompletion.assert_called_once()


@pytest.mark.asyncio
async def test_generate_error_handling(router, mock_prompt_chain):
    """Test error handling during generation"""
    error_message = "Test error"
    router.router.acompletion.side_effect = Exception(error_message)

    request = GenerationRequest(
        prompt_chain=mock_prompt_chain, model_name=SupportedLLMModels.GPT_4O
    )

    with pytest.raises(GenerationError) as exc_info:
        await router.generate(request)

    assert f"Error generating response: {error_message}" in str(exc_info.value)


@pytest.fixture
def response_model():
    class _ResponseModel(BaseModel):
        name: str
        value: int

    return _ResponseModel


@pytest.mark.asyncio
async def test_generate_with_structured_response(
    router, response_model, mock_litellm_response, mock_prompt_chain
):
    """Test generation with structured response parsing"""
    # Set up the mock response
    mock_response_content = '{"name": "test", "value": 42}'
    mock_litellm_response.choices[0].message.content = mock_response_content
    router.router.acompletion.return_value = mock_litellm_response

    # Update mock_prompt_chain for structured response
    mock_prompt_chain.parse_response.return_value = response_model(
        name="test", value=42
    )

    request = GenerationRequest(
        prompt_chain=mock_prompt_chain,
        model_name=SupportedLLMModels.GPT_4O,
    )

    response = await router.generate(request)

    assert response.content == mock_response_content
    assert isinstance(response.parsed_response, response_model)
    assert response.parsed_response.name == "test"
    assert response.parsed_response.value == 42


@pytest.mark.asyncio
async def test_generate_with_max_tokens(
    router, mock_prompt_chain, mock_litellm_response
):
    """Test generation with max tokens parameter"""
    mock_litellm_response.choices[0].message.content = '{"response": "Test response"}'
    router.router.acompletion.return_value = mock_litellm_response

    request = GenerationRequest(
        prompt_chain=mock_prompt_chain,
        model_name=SupportedLLMModels.GPT_4O,
        max_tokens=100,
    )

    await router.generate(request)

    # Verify max_tokens was passed to the completion params
    router.router.acompletion.assert_called_once()
    call_args = router.router.acompletion.call_args[1]
    assert call_args["max_tokens"] == 100


@pytest.mark.asyncio
async def test_generate_with_temperature(
    router, mock_prompt_chain, mock_litellm_response
):
    """Test generation with temperature parameter"""
    mock_litellm_response.choices[0].message.content = '{"response": "Test response"}'
    router.router.acompletion.return_value = mock_litellm_response

    request = GenerationRequest(
        prompt_chain=mock_prompt_chain,
        model_name=SupportedLLMModels.GPT_4O,
        temperature=0.7,
    )

    await router.generate(request)

    # Verify temperature was passed to the completion params
    router.router.acompletion.assert_called_once()
    call_args = router.router.acompletion.call_args[1]
    assert call_args["temperature"] == 0.7


@pytest.fixture
def mock_embedding_response():
    """Create a mock embedding response from LiteLLM."""
    return Mock(
        data=[Mock(embedding=[0.1, 0.2, 0.3, 0.4, 0.5], index=0)],
        model="text-embedding-ada-002-v2",
        usage=Mock(prompt_tokens=10, total_tokens=10),
    )


@pytest.fixture
def mock_embedding_response_dict():
    """Create a mock embedding response as a dictionary."""
    return {
        "object": "list",
        "data": [
            {"object": "embedding", "index": 0, "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]}
        ],
        "model": "text-embedding-ada-002-v2",
        "usage": {"prompt_tokens": 10, "total_tokens": 10},
    }


@pytest.fixture
def router_with_embeddings(mock_settings):
    """Create a router with embedding support configured."""
    mock_router = Mock()
    mock_router.acompletion = AsyncMock()
    mock_router.aembedding = AsyncMock()

    with patch("litellm.Router", return_value=mock_router), patch(
        "pantheon_v2.core.modelrouter.providers.litellm.router.LiteLLMRouter._setup_router"
    ), patch(
        "pantheon_v2.core.modelrouter.providers.litellm.router.EmbeddingProviderMapping.get_provider_configs"
    ) as mock_embedding_configs:
        # Mock the embedding provider configs - use only the available model
        mock_embedding_configs.return_value = {
            SupportedEmbeddingsModels.OPENAI_EMBEDDINGS: [
                Mock(model_id="text-embedding-3-large", dimensions=1536)
            ]
        }

        router = LiteLLMRouter(settings=mock_settings)
        router.router = mock_router
        # Set up adapter
        router.adapter = Mock()
        router.adapter.from_embedding_response.return_value = EmbeddingResponse(
            data=[
                EmbeddingData(
                    embedding=[0.1, 0.2, 0.3, 0.4, 0.5], index=0, object="embedding"
                )
            ],
            model=SupportedEmbeddingsModels.OPENAI_EMBEDDINGS.value,
            usage=Usage(prompt_tokens=10, completion_tokens=0, total_tokens=10),
            raw_response={},
        )
        return router


@pytest.mark.asyncio
async def test_generate_text_embeddings(
    router_with_embeddings, mock_embedding_response_dict
):
    """Test generating text embeddings."""
    router = router_with_embeddings
    router.router.aembedding.return_value = mock_embedding_response_dict

    # Create a text embedding request
    request = EmbeddingRequest(
        model_name=SupportedEmbeddingsModels.OPENAI_EMBEDDINGS,
        input=EmbeddingInput(type=InputType.TEXT, content="Test text for embeddings"),
    )

    # Generate embeddings
    response = await router.generate_embeddings(request)

    # Verify the API was called correctly
    router.router.aembedding.assert_called_once()
    call_args = router.router.aembedding.call_args[1]
    assert call_args["model"] == SupportedEmbeddingsModels.OPENAI_EMBEDDINGS.value
    assert call_args["input"] == "Test text for embeddings"

    # Verify the response
    assert isinstance(response, EmbeddingResponse)
    assert response.model == SupportedEmbeddingsModels.OPENAI_EMBEDDINGS.value
    assert len(response.data) == 1
    assert response.data[0].embedding == [0.1, 0.2, 0.3, 0.4, 0.5]


@pytest.mark.asyncio
async def test_generate_image_embeddings(
    router_with_embeddings, mock_embedding_response_dict
):
    """Test generating image embeddings."""
    router = router_with_embeddings
    router.router.aembedding.return_value = mock_embedding_response_dict

    # Create a simple base64 image
    base64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

    # Use the available model for image embeddings too
    model_name = SupportedEmbeddingsModels.OPENAI_EMBEDDINGS

    # Create an image embedding request
    request = EmbeddingRequest(
        model_name=model_name,
        input=EmbeddingInput(
            type=InputType.IMAGE, content=ImageInput(base64_data=base64_data)
        ),
    )

    # Mock the file type inference
    with patch(
        "pantheon_v2.core.modelrouter.providers.litellm.router.infer_file_type"
    ) as mock_infer:
        mock_infer.return_value = "image/png"

        # Generate embeddings
        response = await router.generate_embeddings(request)

    # Verify the API was called correctly
    router.router.aembedding.assert_called_once()
    call_args = router.router.aembedding.call_args[1]
    assert call_args["model"] == model_name.value
    assert call_args["input"].startswith("data:image/png;base64,")

    # Verify the response
    assert isinstance(response, EmbeddingResponse)
    assert response.model == model_name.value
    assert len(response.data) == 1
    assert response.data[0].embedding == [0.1, 0.2, 0.3, 0.4, 0.5]


@pytest.mark.asyncio
async def test_embedding_error_handling(router_with_embeddings):
    """Test error handling in embedding generation."""
    router = router_with_embeddings

    # Configure the mock to raise an exception
    router.router.aembedding.side_effect = Exception("Test embedding error")

    # Create a text embedding request
    request = EmbeddingRequest(
        model_name=SupportedEmbeddingsModels.OPENAI_EMBEDDINGS,
        input=EmbeddingInput(type=InputType.TEXT, content="Test text for embeddings"),
    )

    # Verify that the error is properly wrapped
    with pytest.raises(EmbeddingError) as exc_info:
        await router.generate_embeddings(request)

    assert "Test embedding error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_embeddings_with_adapter(
    router_with_embeddings, mock_embedding_response_dict
):
    """Test that the adapter is used to process embedding responses."""
    router = router_with_embeddings
    router.router.aembedding.return_value = mock_embedding_response_dict

    # Reset the mock to test the actual call
    router.adapter.from_embedding_response.reset_mock()

    # Set up the mock to return a specific response for this test
    router.adapter.from_embedding_response.return_value = EmbeddingResponse(
        data=[EmbeddingData(embedding=[0.9, 0.8, 0.7], index=0, object="embedding")],
        model=SupportedEmbeddingsModels.OPENAI_EMBEDDINGS.value,
        usage=Usage(prompt_tokens=5, completion_tokens=0, total_tokens=5),
        raw_response=mock_embedding_response_dict,
    )

    # Create a text embedding request
    request = EmbeddingRequest(
        model_name=SupportedEmbeddingsModels.OPENAI_EMBEDDINGS,
        input=EmbeddingInput(
            type=InputType.TEXT, content="Test adapter with embeddings"
        ),
    )

    # Generate embeddings
    response = await router.generate_embeddings(request)

    # Verify the adapter was called
    router.adapter.from_embedding_response.assert_called_once_with(
        mock_embedding_response_dict, SupportedEmbeddingsModels.OPENAI_EMBEDDINGS.value
    )

    # Verify we got the adapter's response
    assert response.data[0].embedding == [0.9, 0.8, 0.7]
    assert response.usage.prompt_tokens == 5


@pytest.mark.parametrize(
    "input_metadata,trace_id,expected_result",
    [
        (None, "test-trace-id", {"session_id": "test-trace-id"}),
        ({}, "test-trace-id", {"session_id": "test-trace-id"}),
        (
            {"existing": "value"},
            "test-trace-id",
            {"existing": "value", "session_id": "test-trace-id"},
        ),
        ({"existing": "value"}, None, {"existing": "value"}),
    ],
)
def test_add_trace_id_to_metadata(router, input_metadata, trace_id, expected_result):
    """Test adding trace ID to metadata."""
    with patch(
        "pantheon_v2.core.modelrouter.providers.litellm.router.get_trace_id",
        return_value=trace_id,
    ):
        result = router._add_trace_id_to_metadata(input_metadata)

        # Verify the result matches expected output
        assert result == expected_result

        # If trace_id is not None, verify it was added as session_id
        if trace_id:
            assert "session_id" in result
            assert result["session_id"] == trace_id
        # If input_metadata had existing values, verify they're preserved
        if input_metadata and "existing" in input_metadata:
            assert "existing" in result
            assert result["existing"] == input_metadata["existing"]
