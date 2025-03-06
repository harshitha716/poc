import unittest
from unittest.mock import patch, mock_open
import yaml
import json
from pantheon.ai_agents.tools.herm.tool import HermTool


class TestHermTool(unittest.TestCase):
    def setUp(self):
        self.tool = HermTool()

    @patch("pantheon.ai_agents.tools.herm.tool.settings")
    def test_init(self, mock_settings):
        mock_settings.HERM_PROXY_URL = "http://test-url.com"
        mock_settings.ENVIRONMENT = "TEST"

        tool = HermTool()

        self.assertEqual(tool.base_url, "http://test-url.com")
        self.assertEqual(tool.sheet_sub_url, "page/sheet")
        self.assertEqual(tool.env, "TEST")

    @patch(
        "pantheon.ai_agents.tools.herm.tool.open",
        new_callable=mock_open,
        read_data='{"key": "value"}',
    )
    @patch("pantheon.ai_agents.tools.herm.tool.json.load")
    def test_load_context(self, mock_json_load, mock_file):
        mock_json_load.return_value = {"key": "value"}
        result = self.tool._load_context()
        self.assertEqual(result, {"key": "value"})

    @patch("pantheon.ai_agents.tools.herm.tool.open", side_effect=FileNotFoundError)
    def test_load_context_file_not_found(self, mock_file):
        with self.assertRaises(FileNotFoundError):
            self.tool._load_context()

    @patch(
        "pantheon.ai_agents.tools.herm.tool.open",
        new_callable=mock_open,
        read_data="{invalid json}",
    )
    def test_load_context_json_decode_error(self, mock_file):
        with self.assertRaises(json.JSONDecodeError):
            self.tool._load_context()

    @patch("pantheon.ai_agents.tools.herm.tool.get")
    def test_make_get_request_success(self, mock_get):
        mock_get.return_value = {"key": "value"}
        result = self.tool._make_get_request("test_url")
        self.assertEqual(result, {"key": "value"})

    @patch("pantheon.ai_agents.tools.herm.tool.get")
    def test_make_get_request_failure(self, mock_get):
        mock_get.side_effect = Exception("Test exception")
        result = self.tool._make_get_request("test_url")
        self.assertIsNone(result)

    @patch(
        "pantheon.ai_agents.tools.herm.tool.open",
        new_callable=mock_open,
        read_data="key: value",
    )
    @patch("pantheon.ai_agents.tools.herm.tool.yaml.safe_load")
    @patch("pantheon.ai_agents.tools.herm.tool.yaml.safe_dump")
    def test_get_herm_formulas(self, mock_safe_dump, mock_safe_load, mock_file):
        mock_safe_load.return_value = {"key": "value"}
        mock_safe_dump.return_value = "key: value\n"

        result = self.tool.get_herm_formulas()
        self.assertEqual(result, "key: value\n")

    @patch("pantheon.ai_agents.tools.herm.tool.open", side_effect=FileNotFoundError)
    def test_get_herm_formulas_file_not_found(self, mock_file):
        with self.assertRaises(FileNotFoundError):
            self.tool.get_herm_formulas()

    @patch(
        "pantheon.ai_agents.tools.herm.tool.open",
        new_callable=mock_open,
        read_data="{invalid: yaml",
    )
    def test_get_herm_formulas_yaml_error(self, mock_file):
        with self.assertRaises(yaml.YAMLError):
            self.tool.get_herm_formulas()

    @patch(
        "pantheon.ai_agents.tools.herm.tool.open",
        new_callable=mock_open,
        read_data="key: value",
    )
    @patch("pantheon.ai_agents.tools.herm.tool.yaml.safe_load")
    @patch("pantheon.ai_agents.tools.herm.tool.yaml.safe_dump")
    def test_get_herm_transformations(self, mock_safe_dump, mock_safe_load, mock_file):
        mock_safe_load.return_value = {"key": "value"}
        mock_safe_dump.return_value = "key: value\n"

        result = self.tool.get_herm_transformations()
        self.assertEqual(result, "key: value\n")

    @patch("pantheon.ai_agents.tools.herm.tool.open", side_effect=FileNotFoundError)
    def test_get_herm_transformations_file_not_found(self, mock_file):
        with self.assertRaises(FileNotFoundError):
            self.tool.get_herm_transformations()

    @patch(
        "pantheon.ai_agents.tools.herm.tool.open",
        new_callable=mock_open,
        read_data="{invalid: yaml",
    )
    def test_get_herm_transformations_yaml_error(self, mock_file):
        with self.assertRaises(yaml.YAMLError):
            self.tool.get_herm_transformations()

    def test_update_sheet_context_invalid_context(self):
        action = {"name": "TEST_ACTION", "params": []}
        sheet_context = "invalid_context"
        result = self.tool.update_sheet_context(action, sheet_context)
        self.assertEqual(result, "invalid_context")

    def test_update_sheet_context_no_tables(self):
        action = {"name": "TEST_ACTION", "params": []}
        sheet_context = {"no_tables": True}
        result = self.tool.update_sheet_context(action, sheet_context)
        self.assertEqual(result, {"no_tables": True})

    def test_update_sheet_context_unknown_action(self):
        action = {"name": "UNKNOWN_ACTION", "params": []}
        sheet_context = {"tables": [{"range": "A1:B2", "columns": []}]}
        result = self.tool.update_sheet_context(action, sheet_context)
        self.assertEqual(result, sheet_context)

    def test_add_column(self):
        params = {"column_index": "B", "no_of_columns": "1"}
        sheet_context = {
            "tables": [
                {
                    "range": "A1:B3",
                    "total_columns": 2,
                    "total_rows": 3,
                    "columns": [
                        {"header": "Col1", "id": "A", "sample_values": ["1", "2"]},
                        {"header": "Col2", "id": "B", "sample_values": ["3", "4"]},
                    ],
                }
            ]
        }
        result = self.tool._add_column(sheet_context, params)
        self.assertEqual(result["tables"][0]["range"], "A1:C3")
        self.assertEqual(result["tables"][0]["total_columns"], 3)
        self.assertEqual(len(result["tables"][0]["columns"]), 3)

    def test_remove_column(self):
        params = {"column_index": "B"}
        sheet_context = {
            "tables": [
                {
                    "range": "A1:C3",
                    "total_columns": 3,
                    "columns": [
                        {"header": "Col1", "id": "A", "sample_values": ["1", "2"]},
                        {"header": "Col2", "id": "B", "sample_values": ["3", "4"]},
                        {"header": "Col3", "id": "C", "sample_values": ["5", "6"]},
                    ],
                }
            ]
        }
        result = self.tool._remove_column(sheet_context, params)
        self.assertEqual(result["tables"][0]["range"], "A1:B3")
        self.assertEqual(result["tables"][0]["total_columns"], 2)
        self.assertEqual(len(result["tables"][0]["columns"]), 2)

    def test_update_cell(self):
        params = {"cell_index": "A1", "new_value": "New Header"}
        sheet_context = {
            "tables": [
                {
                    "range": "A1:B3",
                    "columns": [
                        {"header": "Col1", "id": "A", "sample_values": ["1", "2"]},
                        {"header": "Col2", "id": "B", "sample_values": ["3", "4"]},
                    ],
                }
            ]
        }
        result = self.tool._update_cell(sheet_context, params)
        self.assertEqual(result["tables"][0]["columns"][0]["header"], "New Header")

    def test_add_row(self):
        params = {"row_index": "1", "no_of_rows": "2"}
        sheet_context = {
            "tables": [
                {
                    "range": "A1:B3",
                    "total_rows": 3,
                    "columns": [
                        {"header": "Col1", "id": "A", "sample_values": ["1", "2"]},
                        {"header": "Col2", "id": "B", "sample_values": ["3", "4"]},
                    ],
                }
            ]
        }
        result = self.tool._add_row(sheet_context, params)
        self.assertEqual(result["tables"][0]["range"], "A1:B5")
        self.assertEqual(result["tables"][0]["total_rows"], 5)
        self.assertEqual(len(result["tables"][0]["columns"][0]["sample_values"]), 2)

    def test_remove_row(self):
        params = {"row_index": "2"}
        sheet_context = {
            "tables": [
                {
                    "range": "A1:B4",
                    "total_rows": 4,
                    "columns": [
                        {"header": "Col1", "id": "A", "sample_values": ["1", "2", "3"]},
                        {"header": "Col2", "id": "B", "sample_values": ["4", "5", "6"]},
                    ],
                }
            ]
        }
        result = self.tool._remove_row(sheet_context, params)
        self.assertEqual(result["tables"][0]["range"], "A1:B3")
        self.assertEqual(result["tables"][0]["total_rows"], 3)
        self.assertEqual(len(result["tables"][0]["columns"][0]["sample_values"]), 2)

    def test_get_start_column_id(self):
        self.assertEqual(self.tool._get_start_column_id("A1:B2"), "A")
        self.assertEqual(self.tool._get_start_column_id("AB123:CD456"), "AB")
        self.assertEqual(self.tool._get_start_column_id("123"), "A")

    def test_update_table_range(self):
        table = {"range": "A1:B3", "columns": [{"id": "A"}, {"id": "B"}, {"id": "C"}]}
        self.tool._update_table_range(table)
        self.assertEqual(table["range"], "A1:C3")

    def test_split_cell_reference(self):
        self.assertEqual(self.tool._split_cell_reference("A1"), ("A", "1"))
        self.assertEqual(self.tool._split_cell_reference("BC23"), ("BC", "23"))
        with self.assertRaises(ValueError):
            self.tool._split_cell_reference("Invalid")

    def test_is_column_in_range(self):
        self.assertTrue(self.tool._is_column_in_range("B", "A", "C"))
        self.assertFalse(self.tool._is_column_in_range("D", "A", "C"))

    def test_column_to_index(self):
        self.assertEqual(self.tool._column_to_index("A"), 0)
        self.assertEqual(self.tool._column_to_index("Z"), 25)
        self.assertEqual(self.tool._column_to_index("AA"), 26)

    def test_index_to_column(self):
        self.assertEqual(self.tool._index_to_column(0), "A")
        self.assertEqual(self.tool._index_to_column(25), "Z")
        self.assertEqual(self.tool._index_to_column(26), "AA")
        with self.assertRaises(ValueError):
            self.tool._index_to_column(-1)

    def test_increment_column_id(self):
        self.assertEqual(self.tool._increment_column_id("A", 1), "B")
        self.assertEqual(self.tool._increment_column_id("Z", 1), "AA")
        self.assertEqual(self.tool._increment_column_id("", 1), "A")
        self.assertEqual(self.tool._increment_column_id("A", 0), "A")  # New test case
        self.assertEqual(self.tool._increment_column_id("B", 2), "D")  # New test case
        self.assertEqual(self.tool._increment_column_id("AA", 1), "AB")  # New test case
