import unittest
from unittest.mock import patch, MagicMock
from openai import OpenAI
from pantheon.ai_agents.internal.llm_service.schemas.llm import LLMMessageResponse
from pantheon.ai_agents.internal.llm_service.exceptions import NoLLMResponse
from pantheon.ai_agents.internal.llm_service.providers.openai import OpenAIClient
from dotenv import load_dotenv

load_dotenv()


class TestOpenAIClient(unittest.TestCase):
    @patch.object(OpenAI, "__init__", lambda self, api_key: None)
    def setUp(self, mock_api_key="sk---"):
        self.client = OpenAIClient()
        self.client.client = MagicMock()

    def test_send_message_success(self):
        messages = [{"role": "user", "content": "Hello"}]
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Hi", role="assistant"))
        ]
        self.client.client.chat.completions.create.return_value = mock_response

        response = self.client.send_message(messages)

        self.assertIsInstance(response, LLMMessageResponse)
        self.assertEqual(response.content, "Hi")
        self.assertEqual(response.role, "assistant")

    def test_send_message_no_response(self):
        messages = [{"role": "user", "content": "Hello"}]
        mock_response = MagicMock()
        mock_response.choices = []
        self.client.client.chat.completions.create.return_value = mock_response

        response = self.client.send_message(messages)

        self.assertIsInstance(response, NoLLMResponse)

    def test_send_message_exception(self):
        messages = [{"role": "user", "content": "Hello"}]
        self.client.client.chat.completions.create.side_effect = Exception("API error")

        with self.assertRaises(Exception) as context:
            self.client.send_message(messages)

        self.assertEqual(str(context.exception), "API error")
