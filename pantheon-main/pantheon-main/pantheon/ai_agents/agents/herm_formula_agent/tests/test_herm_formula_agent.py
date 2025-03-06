import unittest
from unittest.mock import patch
from pantheon.ai_agents.agents.herm_formula_agent.herm_formula_agent import (
    HermFormulaAgent,
)
from pantheon.ai_agents.agents.herm_formula_agent.schemas.formula_agent import (
    HermFormulaAgentResponse,
)


class TestHermFormulaAgent(unittest.TestCase):
    def setUp(self):
        self.agent = HermFormulaAgent()

    @patch(
        "pantheon.ai_agents.agents.herm_formula_agent.herm_formula_agent.open",
        new_callable=unittest.mock.mock_open,
        read_data="Test system prompt",
    )
    def test_load_system_prompt(self, mock_open):
        result = self.agent._load_system_prompt()
        self.assertEqual(result, "Test system prompt")
        mock_open.assert_called_once()

    @patch(
        "pantheon.ai_agents.agents.herm_formula_agent.herm_formula_agent.open",
        side_effect=FileNotFoundError,
    )
    def test_load_system_prompt_file_not_found(self, mock_open):
        with self.assertRaises(FileNotFoundError):
            self.agent._load_system_prompt()

    @patch.object(HermFormulaAgent, "_create_herm_formula_prompt")
    @patch.object(HermFormulaAgent, "_query_llm_service")
    @patch.object(HermFormulaAgent, "_parse_llm_response")
    def test_process_user_input_success(self, mock_parse, mock_query, mock_create):
        mock_create.return_value = [{"role": "user", "content": "test prompt"}]
        mock_query.return_value = "LLM response"
        mock_parse.return_value = HermFormulaAgentResponse(
            formula="=SUM(A1:A10)", explanation="Sum of A1 to A10"
        )

        query = "Sum column A"
        context = {"data": [{"A": 1}, {"A": 2}]}
        result = self.agent.process_user_input(query, context)

        self.assertEqual(result.formula, "=SUM(A1:A10)")
        self.assertEqual(result.explanation, "Sum of A1 to A10")

    @patch.object(HermFormulaAgent, "_create_herm_formula_prompt")
    @patch.object(HermFormulaAgent, "_query_llm_service")
    def test_process_user_input_exception(self, mock_query, mock_create):
        mock_create.return_value = [{"role": "user", "content": "test prompt"}]
        mock_query.side_effect = Exception("LLM error")

        query = "Sum column A"
        context = {"data": [{"A": 1}, {"A": 2}]}
        result = self.agent.process_user_input(query, context)

        self.assertEqual(result.formula, "")
        self.assertEqual(result.explanation, "Sorry we couldn't fulfil your request")

    @patch("pantheon.ai_agents.agents.herm_formula_agent.herm_formula_agent.HermTool")
    def test_create_herm_formula_prompt(self, mock_herm_tool):
        mock_herm_tool.return_value.get_herm_formulas.return_value = {
            "SUM": "Adds numbers"
        }
        self.agent.system_prompt = (
            "System prompt with {{USER_QUERY}} and {{FUNCTION_LIBRARY}} and {{CONTEXT}}"
        )

        query = "Sum column A"
        context = {"context": "Sheet data", "data": [{"A": 1}, {"A": 2}]}
        result = self.agent._create_herm_formula_prompt(query, context)

        # Check if the result is a list with one dictionary
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], dict)

        # Check if the dictionary has the correct keys
        self.assertIn("role", result[0])
        self.assertIn("content", result[0])

        # Check if the role is correct
        self.assertEqual(result[0]["role"], "user")

        # Check if the content contains the expected parts
        content = result[0]["content"]
        self.assertIn("System prompt with Sum column A", content)

    def test_parse_llm_response_success(self):
        response_dict = {"formula": "SUM(A1:A10)", "explanation": "Sum of A1 to A10"}
        result = self.agent._parse_llm_response(response_dict)
        self.assertEqual(result.formula, "=SUM(A1:A10)")

    def test_parse_llm_response_no_formula(self):
        response_dict = {"explanation": "No formula found"}
        result = self.agent._parse_llm_response(response_dict)
        self.assertEqual(result.formula, "FORMULA_NOT_FOUND")

    def test_parse_llm_response_none(self):
        result = self.agent._parse_llm_response(None)
        self.assertEqual(result.formula, "FORMULA_NOT_FOUND")

    def test_decorate_formula(self):
        formula = "SUM(A1:A10)"
        result = self.agent._decorate_formula(formula)
        self.assertEqual(result, "=SUM(A1:A10)")

    def test_decorate_formula_not_found(self):
        formula = "FORMULA_NOT_FOUND"
        result = self.agent._decorate_formula(formula)
        self.assertEqual(result, "FORMULA_NOT_FOUND")
