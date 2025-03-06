from unittest.mock import Mock

from pantheon_v2.core.modelrouter.models.models import EmbeddingResponse
from pantheon_v2.core.modelrouter.providers.litellm.adapter import LiteLLMAdapter


class MockUsage:
    def __init__(self):
        self.prompt_tokens = 10
        self.total_tokens = 10

    def to_dict(self):
        return {"prompt_tokens": self.prompt_tokens, "total_tokens": self.total_tokens}


class MockDataItem:
    def __init__(self):
        self.embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.index = 0


class MockResponse:
    def __init__(self):
        self.model = "text-embedding-ada-002-v2"
        self.data = [MockDataItem()]
        self.usage = MockUsage()


class TestLiteLLMAdapter:
    """Tests for the LiteLLM adapter functionality."""

    def setup_method(self):
        """Set up the adapter for each test."""
        self.adapter = LiteLLMAdapter()

    def test_from_embedding_response_dict(self):
        """Test parsing a dictionary embedding response."""
        # Create a mock response as a dictionary
        mock_response = {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "index": 0,
                    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                }
            ],
            "model": "text-embedding-ada-002-v2",
            "usage": {"prompt_tokens": 10, "total_tokens": 10},
        }

        # Parse the response
        result = self.adapter.from_embedding_response(mock_response, "test-model")

        # Verify the result
        assert isinstance(result, EmbeddingResponse)
        assert result.model == "text-embedding-ada-002-v2"
        assert len(result.data) == 1
        assert result.data[0].embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert result.data[0].index == 0
        assert result.usage.prompt_tokens == 10
        assert result.usage.total_tokens == 10

    def test_from_embedding_response_object(self):
        """Test parsing an object embedding response."""
        # Create a class to simulate the real response object structure

        # Create an instance of our mock response
        mock_response = MockResponse()

        # Parse the response
        result = self.adapter.from_embedding_response(mock_response, "test-model")

        # Verify the result
        assert isinstance(result, EmbeddingResponse)
        assert result.model == "text-embedding-ada-002-v2"
        assert len(result.data) == 1
        assert result.data[0].embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert result.data[0].index == 0
        assert result.usage.prompt_tokens == 10
        assert result.usage.total_tokens == 10

    def test_from_embedding_response_with_to_dict(self):
        """Test parsing a response with to_dict method."""
        # Create a mock response with to_dict method
        mock_response = Mock()
        mock_response.to_dict.return_value = {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "index": 0,
                    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                }
            ],
            "model": "text-embedding-ada-002-v2",
            "usage": {"prompt_tokens": 10, "total_tokens": 10},
        }

        # Parse the response
        result = self.adapter.from_embedding_response(mock_response, "test-model")

        # Verify the result
        assert isinstance(result, EmbeddingResponse)
        assert result.model == "text-embedding-ada-002-v2"
        assert len(result.data) == 1
        assert result.data[0].embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert result.data[0].index == 0
        assert result.usage.prompt_tokens == 10
        assert result.usage.total_tokens == 10
