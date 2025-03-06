import unittest
from unittest.mock import MagicMock, patch
from pantheon.ai_agents.internal.llm_service.service import LLMService
from pantheon.ai_agents.internal.llm_service.enums.llmclient import LLMClientType
from pantheon.ai_agents.internal.llm_service.providers.openai import OpenAIClient
from pantheon.ai_agents.internal.llm_service.exceptions import (
    InvalidLLMClientType,
    NoLLMClientInitialised,
)
from pantheon.ai_agents.internal.llm_service.schemas.llm import LLMMessageResponse


class TestLLMService(unittest.TestCase):
    @patch(
        "pantheon.ai_agents.internal.llm_service.service.OpenAIClient",
        spec=OpenAIClient,
    )
    def test_initialization_with_openai_client(self, MockOpenAIClient):
        service = LLMService(LLMClientType.OPENAI)
        self.assertIsInstance(service.client, OpenAIClient)
        MockOpenAIClient.assert_called_once()

    def test_initialization_with_invalid_client_type(self):
        with self.assertRaises(InvalidLLMClientType):
            LLMService("invalid_client_type")

    @patch(
        "pantheon.ai_agents.internal.llm_service.service.OpenAIClient",
        spec=OpenAIClient,
    )
    def test_send_message_with_initialized_client(self, MockOpenAIClient):
        mock_openai_client = MockOpenAIClient.return_value
        mock_response = MagicMock(spec=LLMMessageResponse)
        mock_openai_client.send_message.return_value = mock_response

        service = LLMService(LLMClientType.OPENAI)

        messages = [{"role": "user", "content": "Hello"}]
        model = "gpt-3.5-turbo"

        response = service.send_message(messages, model)

        self.assertEqual(response, mock_response)
        mock_openai_client.send_message.assert_called_once_with(messages, model)

    def test_send_message_without_initialized_client(self):
        service = LLMService.__new__(LLMService)
        service.client = None  # Manually set client attribute to None

        messages = [{"role": "user", "content": "Hello"}]
        model = "gpt-3.5-turbo"

        with self.assertRaises(NoLLMClientInitialised):
            service.send_message(messages, model)

    @patch(
        "pantheon.ai_agents.internal.llm_service.service.OpenAIClient",
        spec=OpenAIClient,
    )
    def test_initialization_with_none_client_type(self, MockOpenAIClient):
        with self.assertRaises(InvalidLLMClientType):
            LLMService(None)

    @patch(
        "pantheon.ai_agents.internal.llm_service.service.OpenAIClient",
        spec=OpenAIClient,
    )
    def test_send_message_with_empty_message_list(self, MockOpenAIClient):
        mock_openai_client = MockOpenAIClient.return_value
        mock_response = MagicMock(spec=LLMMessageResponse)
        mock_openai_client.send_message.return_value = mock_response

        service = LLMService(LLMClientType.OPENAI)

        messages = []  # Empty message list
        model = "gpt-3.5-turbo"

        response = service.send_message(messages, model)

        self.assertEqual(response, mock_response)
        mock_openai_client.send_message.assert_called_once_with(messages, model)

    @patch(
        "pantheon.ai_agents.internal.llm_service.service.OpenAIClient",
        spec=OpenAIClient,
    )
    def test_send_message_with_api_failure(self, MockOpenAIClient):
        mock_openai_client = MockOpenAIClient.return_value
        mock_openai_client.send_message.side_effect = Exception("API failure")

        service = LLMService(LLMClientType.OPENAI)

        messages = [{"role": "user", "content": "Hello"}]
        model = "gpt-3.5-turbo"

        with self.assertRaises(
            Exception
        ):  # Replace with specific exception if available
            service.send_message(messages, model)

    @patch(
        "pantheon.ai_agents.internal.llm_service.service.OpenAIClient",
        spec=OpenAIClient,
    )
    def test_send_message_with_non_dict_messages(self, MockOpenAIClient):
        mock_openai_client = MockOpenAIClient.return_value
        mock_response = MagicMock(spec=LLMMessageResponse)
        mock_openai_client.send_message.return_value = mock_response

        service = LLMService(LLMClientType.OPENAI)

        messages = ["This is not a dict"]  # Non-dict messages
        model = "gpt-3.5-turbo"

        with self.assertRaises(TypeError):
            service.send_message(messages, model)

    def test_initialization_with_different_types(self):
        for invalid_client_type in [123, 3.14, {}, [], True, False]:
            with self.assertRaises(InvalidLLMClientType):
                LLMService(invalid_client_type)
