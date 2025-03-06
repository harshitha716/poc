import unittest
from unittest.mock import Mock, patch
import uuid
import json
from pantheon.ai_agents.agent_service import AgentService
from pantheon.ai_agents.constants.agent_service_enums import Actions, Status
from pantheon.ai_agents.schemas.agent_schema import (
    TransformationsActionsResponse,
    Action,
    Param,
)


class TestAgentService(unittest.TestCase):
    def setUp(self):
        self.agent_service = AgentService()

    @patch("pantheon.ai_agents.agent_service.HermTool")
    @patch("pantheon.ai_agents.agent_service.HermFormulaAgent")
    def test_get_herm_formula_success(self, MockHermFormulaAgent, MockHermTool):
        # Arrange
        mock_herm_tool = MockHermTool.return_value
        mock_herm_tool.get_sheet_context.return_value = {"mock": "context"}

        mock_formula_agent = MockHermFormulaAgent.return_value
        mock_formula_agent.process_user_input.return_value = Mock(
            formula="=(SUM(A1:A10))",
            explanation="This formula sums up values in A1:A10",
        )

        # Set up the agent_service with mocked dependencies
        self.agent_service.herm_tool = mock_herm_tool
        self.agent_service.herm_formula_agent = mock_formula_agent

        # Act
        result = self.agent_service.get_herm_formula("Sum A1 to A10", uuid.uuid4(), 1)

        # Assert
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertEqual(result.action, Actions.GET_HERM_FORMULA)
        self.assertEqual(result.content, "=(SUM(A1:A10))")
        self.assertEqual(result.explanation, "This formula sums up values in A1:A10")

        # Verify that the mocked methods were called
        mock_herm_tool.get_sheet_context.assert_called_once()
        mock_formula_agent.process_user_input.assert_called_once()

    @patch("pantheon.ai_agents.agent_service.HermTransformationAgent")
    def test_get_herm_transformations_actions(self, MockHermTransformationAgent):
        # Arrange
        mock_transformation_agent = Mock()
        MockHermTransformationAgent.return_value = mock_transformation_agent

        mock_action = Action(
            name="Transform 1",
            params=[Param(name="param1", value="value1")],
            sequence_no=1,
        )

        mock_response = TransformationsActionsResponse(
            status=Status.SUCCESS,
            actions=[mock_action],
        )

        mock_transformation_agent.get_herm_transformations.return_value = mock_response

        # Replace the real HermTransformationAgent with our mock
        self.agent_service.herm_transformation_agent = mock_transformation_agent

        # Act
        test_query = "Transform data"
        test_page_id = uuid.uuid4()
        test_sheet_id = 1
        result = self.agent_service.get_herm_transformations_actions(
            test_query, test_page_id, test_sheet_id
        )

        # Assert
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertEqual(len(result.actions), 1)
        self.assertEqual(result.actions[0].name, "Transform 1")
        self.assertEqual(result.actions[0].params[0].name, "param1")
        self.assertEqual(result.actions[0].params[0].value, "value1")
        self.assertEqual(result.actions[0].sequence_no, 1)

        # Verify that the mock method was called with the correct arguments
        mock_transformation_agent.get_herm_transformations.assert_called_once_with(
            test_query, test_page_id, test_sheet_id
        )

    @patch("pantheon.ai_agents.agent_service.json.load")
    @patch("pantheon.ai_agents.agent_service.open", create=True)
    def test_load_context(self, mock_open, mock_json_load):
        # Arrange
        mock_context = {"key": "value"}
        mock_json_load.return_value = mock_context

        # Act
        result = self.agent_service._load_context()

        # Assert
        mock_open.assert_called_once()
        mock_json_load.assert_called_once()
        self.assertEqual(result, mock_context)

    @patch("pantheon.ai_agents.agent_service.json.load")
    @patch("pantheon.ai_agents.agent_service.open", create=True)
    def test_load_context_file_not_found(self, mock_open, mock_json_load):
        # Arrange
        mock_open.side_effect = FileNotFoundError

        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            self.agent_service._load_context()

    @patch("pantheon.ai_agents.agent_service.json.load")
    @patch("pantheon.ai_agents.agent_service.open", create=True)
    def test_load_context_json_decode_error(self, mock_open, mock_json_load):
        # Arrange
        mock_json_load.side_effect = json.JSONDecodeError("Decode error", "", 0)

        # Act & Assert
        with self.assertRaises(json.JSONDecodeError):
            self.agent_service._load_context()
