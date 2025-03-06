import pytest
from pydantic import BaseModel
from pantheon_v2.core.modelrouter.base import RouterOptions
from pantheon_v2.core.modelrouter.models.models import ModelResponse, GenerationRequest
from pantheon_v2.core.modelrouter.configs.global_llm_config import SupportedLLMModels
from pantheon_v2.core.modelrouter.tests.mock_router import MockModelRouter
from pantheon_v2.core.common.models import MessageRole
from pantheon_v2.core.prompt.chain import PromptChain, ChainConfig
from pantheon_v2.core.prompt.generic import GenericPrompt
from pantheon_v2.core.prompt.models import PromptConfig


class TestResponseModel(BaseModel):
    """Simple response model for testing"""

    message: str


@pytest.fixture
def router():
    return MockModelRouter()


@pytest.fixture
def router_with_options():
    return MockModelRouter(options=RouterOptions())


@pytest.fixture
def basic_prompt_chain():
    # Create a simple prompt chain for testing
    prompt = GenericPrompt(
        config=PromptConfig(
            template="{{input}}", role=MessageRole.USER, variables={"input": "Hello"}
        )
    )

    # Create chain with proper config
    chain = PromptChain(config=ChainConfig(response_model=TestResponseModel))
    chain.add_prompt(prompt)
    return chain


def test_router_initialization():
    router = MockModelRouter()
    assert router.options is not None
    assert isinstance(router.options, RouterOptions)
    assert isinstance(router.supported_models, set)
    assert len(router.supported_models) > 0


def test_router_initialization_with_options():
    options = RouterOptions()
    router = MockModelRouter(options=options)
    assert router.options == options


@pytest.mark.asyncio
async def test_generate_with_string(basic_prompt_chain):
    router = MockModelRouter()
    request = GenerationRequest(
        prompt_chain=basic_prompt_chain,
        model_name=SupportedLLMModels.GPT_4O,
        temperature=None,
        max_tokens=None,
    )
    response = await router.generate(request)
    assert isinstance(response, ModelResponse)
    assert response.content == "test response"
    assert response.model == SupportedLLMModels.GPT_4O


@pytest.mark.asyncio
async def test_generate_with_message_list(basic_prompt_chain):
    router = MockModelRouter()
    request = GenerationRequest(
        prompt_chain=basic_prompt_chain,
        model_name=SupportedLLMModels.GPT_4O,
        temperature=None,
        max_tokens=None,
    )
    response = await router.generate(request)
    assert isinstance(response, ModelResponse)
    assert response.content == "test response"
    assert response.model == SupportedLLMModels.GPT_4O


@pytest.mark.asyncio
async def test_generate_with_temperature(basic_prompt_chain):
    router = MockModelRouter()
    request = GenerationRequest(
        prompt_chain=basic_prompt_chain,
        model_name=SupportedLLMModels.GPT_4O,
        temperature=0.7,
        max_tokens=None,
    )
    response = await router.generate(request)
    assert isinstance(response, ModelResponse)
    assert response.content == "test response"
    assert response.model == SupportedLLMModels.GPT_4O
