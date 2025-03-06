import unittest
from unittest.mock import MagicMock, patch
from pantheon.ai_agents.schemas.agent_schema import AgentQueryResponse
from pantheon.chat import ChatController


class TestChatController(unittest.TestCase):
    @patch("pantheon.ai_agents.agent_service")
    async def test_get_herm_formula_with_valid_query(self, MockAgentService):
        mock_agent_service = MockAgentService.return_value
        mock_response = MagicMock(spec=AgentQueryResponse)
        mock_agent_service.get_herm_formula.return_value = mock_response

        chat_controller = ChatController()
        query = "Sample query"
        response = await chat_controller.get_herm_formula(query)

        mock_agent_service.get_herm_formula.assert_called_once_with(query)
        self.assertEqual(response, mock_response)

    @patch("pantheon.ai_agents.agent_service")
    async def test_get_herm_formula_with_empty_query(self, MockAgentService):
        mock_agent_service = MockAgentService.return_value
        mock_response = MagicMock(spec=AgentQueryResponse)
        mock_agent_service.get_herm_formula.return_value = mock_response

        chat_controller = ChatController()
        query = ""
        response = await chat_controller.get_herm_formula(query)

        mock_agent_service.get_herm_formula.assert_called_once_with(query)
        self.assertEqual(response, mock_response)

    @patch("pantheon.ai_agents.agent_service")
    async def test_get_herm_formula_with_null_query(self, MockAgentService):
        mock_agent_service = MockAgentService.return_value
        mock_response = MagicMock(spec=AgentQueryResponse)
        mock_agent_service.get_herm_formula.return_value = mock_response

        chat_controller = ChatController()
        query = None
        response = await chat_controller.get_herm_formula(query)

        mock_agent_service.get_herm_formula.assert_called_once_with(query)
        self.assertEqual(response, mock_response)

    @patch("pantheon.ai_agents.agent_service")
    async def test_get_herm_formula_with_special_characters(self, MockAgentService):
        mock_agent_service = MockAgentService.return_value
        mock_response = MagicMock(spec=AgentQueryResponse)
        mock_agent_service.get_herm_formula.return_value = mock_response

        chat_controller = ChatController()
        query = "!@#$%^&*()_+-=[]{}|;':,.<>?/~`"
        response = await chat_controller.get_herm_formula(query)

        mock_agent_service.get_herm_formula.assert_called_once_with(query)
        self.assertEqual(response, mock_response)

    @patch("pantheon.ai_agents.agent_service")
    async def test_get_herm_formula_with_service_exception(self, MockAgentService):
        mock_agent_service = MockAgentService.return_value
        mock_agent_service.get_herm_formula.side_effect = Exception("Service failure")

        chat_controller = ChatController()
        query = "Test query"

        with self.assertRaises(Exception) as context:
            await chat_controller.get_herm_formula(query)

        self.assertTrue("Service failure" in str(context.exception))
        mock_agent_service.get_herm_formula.assert_called_once_with(query)
