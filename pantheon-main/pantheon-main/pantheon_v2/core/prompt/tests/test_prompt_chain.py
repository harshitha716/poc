import pytest
from pydantic import BaseModel

from pantheon_v2.core.prompt.chain import PromptChain, ChainConfig
from pantheon_v2.core.prompt.models import PromptConfig
from pantheon_v2.core.prompt.generic import GenericPrompt
from pantheon_v2.core.modelrouter.exceptions.exceptions import GenerationError
from pantheon_v2.core.common.models import MessageRole


class TestResponseModel(BaseModel):
    name: str
    value: int


@pytest.fixture
def response_model():
    return TestResponseModel


@pytest.fixture
def basic_prompt():
    return GenericPrompt(
        config=PromptConfig(
            template="Test template {{OUTPUT_MODEL}}", role=MessageRole.USER
        )
    )


class TestPromptChain:
    def test_initialization(self, response_model):
        chain = PromptChain(config=ChainConfig(response_model=response_model))
        assert chain.config.response_model == response_model
        assert chain.prompts == []

    def test_add_prompt(self, response_model, basic_prompt):
        chain = PromptChain(config=ChainConfig(response_model=response_model))
        result = chain.add_prompt(basic_prompt)

        assert len(chain.prompts) == 1
        assert chain.prompts[0] == basic_prompt
        assert result == chain  # Test method chaining

    def test_build_messages_no_prompts(self, response_model):
        chain = PromptChain(config=ChainConfig(response_model=response_model))
        with pytest.raises(ValueError, match="No prompts added to the chain"):
            chain.build_messages()

    def test_build_messages_no_output_model(self, response_model):
        chain = PromptChain(config=ChainConfig(response_model=response_model))
        prompt = GenericPrompt(
            config=PromptConfig(
                template="Template without output model", role=MessageRole.USER
            )
        )
        chain.add_prompt(prompt)

        with pytest.raises(
            ValueError, match="must contain the {{OUTPUT_MODEL}} placeholder"
        ):
            chain.build_messages()

    def test_build_messages_success(self, response_model, basic_prompt):
        chain = PromptChain(config=ChainConfig(response_model=response_model))
        chain.add_prompt(basic_prompt)

        messages = chain.build_messages()
        assert len(messages) == 1
        assert "<output>" in messages[0].content[0].text
        assert "</output>" in messages[0].content[0].text

    @pytest.mark.parametrize(
        "response,expected",
        [
            ('{"name": "test", "value": 42}', {"name": "test", "value": 42}),
            (
                '```json\n{"name": "test", "value": 42}\n```',
                {"name": "test", "value": 42},
            ),
            (
                '<output>{"name": "test", "value": 42}</output>',
                {"name": "test", "value": 42},
            ),
        ],
    )
    def test_parse_response_variations(self, response_model, response, expected):
        chain = PromptChain(config=ChainConfig(response_model=response_model))
        result = chain.parse_response(response)

        assert isinstance(result, TestResponseModel)
        assert result.name == expected["name"]
        assert result.value == expected["value"]

    def test_parse_response_invalid_json(self, response_model):
        chain = PromptChain(config=ChainConfig(response_model=response_model))
        with pytest.raises(GenerationError):
            chain.parse_response("Invalid JSON")

    def test_parse_response_invalid_schema(self, response_model):
        chain = PromptChain(config=ChainConfig(response_model=response_model))
        with pytest.raises(GenerationError):
            chain.parse_response('{"invalid": "schema"}')

    def test_parse_response_list(self, response_model):
        chain = PromptChain(config=ChainConfig(response_model=response_model))
        response = '[{"name": "test1", "value": 42}, {"name": "test2", "value": 43}]'

        result = chain.parse_response(response)
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, TestResponseModel) for item in result)
