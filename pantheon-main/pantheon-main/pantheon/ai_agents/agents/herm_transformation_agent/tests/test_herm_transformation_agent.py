import unittest
from unittest.mock import patch, MagicMock
import uuid

from pantheon.ai_agents.agents.herm_transformation_agent.herm_transformation_agent import (
    HermTransformationAgent,
)
from pantheon.ai_agents.agents.herm_transformation_agent.schemas.herm_transformation_agent import (
    HermTransformationsActionsResponse,
)


class TestHermTransformationAgent(unittest.TestCase):
    @patch(
        "pantheon.ai_agents.agents.herm_transformation_agent.herm_transformation_agent.LLMService"
    )
    @patch(
        "pantheon.ai_agents.agents.herm_transformation_agent.herm_transformation_agent.HermTool"
    )
    def setUp(self, mock_herm_tool, mock_llm_service):
        self.mock_anthropic_client = MagicMock()
        self.mock_openai_client = MagicMock()
        self.mock_herm_tool = mock_herm_tool.return_value

        mock_llm_service.side_effect = [
            self.mock_anthropic_client,
            self.mock_openai_client,
        ]

        self.agent = HermTransformationAgent()

    def test_get_herm_transformations_success(self):
        # Mock the necessary method calls
        self.agent._get_planning_steps = MagicMock(return_value=["step1", "step2"])
        self.agent._get_herm_context = MagicMock(return_value={})
        self.agent._get_transformation_actions = MagicMock(
            return_value=[
                {
                    "name": "action1",
                    "params": [{"name": "param1", "value": "value1"}],
                    "sequence_no": 1,
                }
            ]
        )

        query = "Test query"
        page_id = uuid.uuid4()
        sheet_id = 1

        result = self.agent.get_herm_transformations(query, page_id, sheet_id)

        self.assertIsInstance(result, HermTransformationsActionsResponse)
        self.assertEqual(len(result.actions), 1)
        self.assertEqual(result.status, "success")

    def test_get_herm_transformations_no_planning_steps(self):
        self.agent._get_planning_steps = MagicMock(return_value=[])

        query = "Test query"
        page_id = uuid.uuid4()
        sheet_id = 1

        result = self.agent.get_herm_transformations(query, page_id, sheet_id)

        self.assertIsInstance(result, HermTransformationsActionsResponse)
        self.assertEqual(len(result.actions), 0)
        self.assertEqual(result.status, "failed")

    @patch(
        "pantheon.ai_agents.agents.herm_transformation_agent.herm_transformation_agent.extract_yaml_from_response"
    )
    def test_get_planning_steps(self, mock_extract_yaml):
        mock_extract_yaml.return_value = {"steps": ["step1", "step2"]}
        self.mock_anthropic_client.send_message.return_value.content = "YAML content"

        result = self.agent._get_planning_steps("Test query")

        self.assertEqual(result, ["step1", "step2"])
        self.mock_anthropic_client.send_message.assert_called_once()

    def test_get_herm_context(self):
        self.mock_herm_tool.get_herm_formulas.return_value = ["formula1"]
        self.mock_herm_tool.get_herm_transformations.return_value = ["transformation1"]
        self.mock_herm_tool.get_sheet_context.return_value = {"key": "value"}

        result = self.agent._get_herm_context(uuid.uuid4(), 1)

        self.assertEqual(
            result,
            {
                "formulas": ["formula1"],
                "transformations": ["transformation1"],
                "sheet_context": {"key": "value"},
            },
        )

    @patch(
        "pantheon.ai_agents.agents.herm_transformation_agent.herm_transformation_agent.extract_yaml_from_response"
    )
    def test_validate_actions(self, mock_extract_yaml):
        mock_extract_yaml.return_value = {"output": [{"confidence_score": 90}]}
        self.mock_anthropic_client.send_message.return_value.content = "YAML content"

        is_valid, additional_context = self.agent._validate_actions("query", [], {})

        self.assertTrue(is_valid)
        self.assertEqual(additional_context, "")

    def test_convert_actions_to_response(self):
        actions = [
            {
                "name": "action1",
                "params": [{"name": "param1", "value": "value1"}],
                "sequence_no": 1,
            },
            {
                "name": "action2",
                "params": [{"name": "param2", "value": "value2"}],
                "sequence_no": 2,
            },
        ]

        result = self.agent._convert_actions_to_response(actions)

        self.assertIsInstance(result, HermTransformationsActionsResponse)
        self.assertEqual(len(result.actions), 2)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.actions[0].name, "action1")
        self.assertEqual(result.actions[0].params[0].name, "param1")
        self.assertEqual(result.actions[0].params[0].value, "value1")
