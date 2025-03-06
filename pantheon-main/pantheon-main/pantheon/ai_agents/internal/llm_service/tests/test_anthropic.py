import unittest
from unittest.mock import patch, MagicMock
from anthropic import Anthropic
from pantheon.ai_agents.internal.llm_service.schemas.llm import LLMMessageResponse
from pantheon.ai_agents.internal.llm_service.exceptions import NoLLMResponse
from pantheon.ai_agents.internal.llm_service.providers.anthropic import AnthropicClient


class TestAnthropicClient(unittest.TestCase):
    @patch.object(Anthropic, "__init__", lambda self, api_key: None)
    def setUp(self, mock_api_key="sk---"):
        self.client = AnthropicClient()
        self.client.client = MagicMock()

    def test_send_message_success(self):
        messages = [{"role": "user", "content": "Hello"}]
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hi")]
        mock_response.role = "assistant"
        self.client.client.messages.create.return_value = mock_response

        response = self.client.send_message(messages)

        self.assertIsInstance(response, LLMMessageResponse)
        self.assertEqual(response.content, "Hi")
        self.assertEqual(response.role, "assistant")

    def test_send_message_no_response(self):
        messages = [{"role": "user", "content": "Hello"}]
        mock_response = MagicMock()
        mock_response.content = []
        self.client.client.messages.create.return_value = mock_response

        response = self.client.send_message(messages)

        self.assertIsInstance(response, NoLLMResponse)

    def test_send_message_exception(self):
        messages = [{"role": "user", "content": "Hello"}]
        self.client.client.messages.create.side_effect = Exception("API error")

        with self.assertRaises(Exception) as context:
            self.client.send_message(messages)

        self.assertEqual(str(context.exception), "API error")
