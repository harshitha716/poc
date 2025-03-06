from typing import Optional
import structlog
from pantheon import settings
from pantheon.settings.settings import DEVELOPMENT, LOCAL
from pantheon.utils.requests import get
import uuid
import os
import yaml
from typing import Dict, Tuple
import json
import re
from pantheon.ai_agents.tools.herm.constants.herm_tool_constants import (
    FUNCTIONS_YAML_FILE_PATH,
    FUNCTIONS_YAML_TRANSFORMATIONS_FILE_PATH,
    CONTEXT_JSON_FILE_PATH,
)

logger = structlog.get_logger(__name__)


class HermTool:
    def __init__(self):
        self.base_url = settings.HERM_PROXY_URL
        self.sheet_sub_url = "page/sheet"
        self.env = settings.ENVIRONMENT

    @staticmethod
    def _load_context() -> Dict:
        filepath = os.path.join(os.path.dirname(__file__), CONTEXT_JSON_FILE_PATH)
        try:
            with open(filepath, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error("HERM_FORMULA_AGENT_ERROR_LOADING_FUNCTIONS", error=str(e))
            raise

    def _make_get_request(self, sub_url: str) -> Optional[dict]:
        try:
            url = f"{self.base_url}/{sub_url}"
            response = get(url=url)
            assert isinstance(response, dict)
            return response
        except Exception as e:
            logger.error("HERM_TOOL_GET_REQUEST_FAILED", url=url, error=e)
            return None

    def get_sheet_context(self, page_id: uuid.UUID, sheet_id: int) -> dict:
        if self.env in (DEVELOPMENT, LOCAL):
            return self._load_context()
        sub_url = f"{page_id}/{self.sheet_sub_url}/{sheet_id}/context/"
        context_response = self._make_get_request(sub_url=sub_url)
        logger.info("HERM_TOOL_GET_SHEET_CONTEXT", context=context_response)
        if not context_response:
            raise Exception("Failed to get context from HERM Tool")
        return context_response

    def get_herm_formulas(self) -> str:
        filepath = os.path.join(os.path.dirname(__file__), FUNCTIONS_YAML_FILE_PATH)
        try:
            with open(filepath, "r") as file:
                data = yaml.safe_load(file)
                return yaml.safe_dump(data, sort_keys=False)
        except FileNotFoundError:
            logger.exception(
                "HERM_TOOL_LOADING_FUNCTIONS_YAML",
                error="File not found",
            )
            raise FileNotFoundError
        except yaml.YAMLError as exc:
            logger.exception("HERM_TOOL_ERROR_LOADING_FUNCTIONS_YAML", error=str(exc))
            raise yaml.YAMLError
        except Exception as e:
            logger.exception("HERM_TOOL_ERROR_LOADING_FUNCTIONS_YAML", error=str(e))
            raise Exception

    def get_herm_transformations(self) -> str:
        filepath = os.path.join(
            os.path.dirname(__file__), FUNCTIONS_YAML_TRANSFORMATIONS_FILE_PATH
        )
        try:
            with open(filepath, "r") as file:
                data = yaml.safe_load(file)
                return yaml.safe_dump(data, sort_keys=False)
        except FileNotFoundError:
            logger.exception(
                "HERM_TOOL_LOADING_FUNCTIONS_YAML",
                error="File not found",
            )
            raise FileNotFoundError
        except yaml.YAMLError as exc:
            logger.exception("HERM_TOOL_LOADING_FUNCTIONS_YAML", error=str(exc))
            raise yaml.YAMLError
        except Exception as e:
            logger.exception("HERM_TOOL_LOADING_FUNCTIONS_YAML", error=str(e))
            raise Exception

    def update_sheet_context(self, action: Dict, sheet_context: Dict) -> Dict:
        if not isinstance(sheet_context, dict):
            logger.error(
                "HERM_TRANSFORMATION_AGENT_ERROR_INVALID_SHEET_CONTEXT_TYPE",
                context_type=type(sheet_context),
            )
            return sheet_context

        if "tables" not in sheet_context or not sheet_context["tables"]:
            logger.warning("HERM_TRANSFORMATION_AGENT_WARNING_NO_TABLES_IN_CONTEXT")
            return sheet_context

        action_name = action["name"]
        params = {param["name"]: param["value"] for param in action["params"]}

        logger.info(
            "HERM_TRANSFORMATION_AGENT_UPDATING_SHEET_CONTEXT",
            action_name=action_name,
            params=params,
        )

        try:
            if action_name == "ADD_COLUMN":
                sheet_context = self._add_column(sheet_context, params)
            elif action_name == "REMOVE_COLUMN":
                sheet_context = self._remove_column(sheet_context, params)
            elif action_name == "UPDATE_CELL":
                sheet_context = self._update_cell(sheet_context, params)
            elif action_name == "ADD_ROW":
                sheet_context = self._add_row(sheet_context, params)
            elif action_name == "REMOVE_ROW":
                sheet_context = self._remove_row(sheet_context, params)
            else:
                logger.warning(
                    "HERM_TRANSFORMATION_AGENT_UNKNOWN_ACTION", action_name=action_name
                )
        except Exception as e:
            logger.error(
                "HERM_TRANSFORMATION_AGENT_ERROR_UPDATING_CONTEXT",
                action_name=action_name,
                error=str(e),
            )
            return sheet_context

        return sheet_context

    def _add_column(self, sheet_context: Dict, params: Dict) -> Dict:
        if "column_index" not in params or "no_of_columns" not in params:
            raise ValueError(
                "ADD_COLUMN requires 'column_name' and 'no_of_columns' in params"
            )

        column_name = params["column_index"]
        no_of_columns = int(params["no_of_columns"])

        for table in sheet_context["tables"]:
            start_col, start_row = self._split_cell_reference(
                table["range"].split(":")[0]
            )
            end_col, end_row = self._split_cell_reference(table["range"].split(":")[1])

            table_start_col = start_col
            table_end_col = end_col

            # Case 1: Columns added at the start of the table (empty column_name)
            if column_name == "":
                new_end_col = self._increment_column_id(table_end_col, no_of_columns)
                table["range"] = f"{start_col}{start_row}:{new_end_col}{end_row}"
                table["total_columns"] += no_of_columns
                for i in range(no_of_columns):
                    new_column = {
                        "header": f"New Column {i+1}",
                        "id": self._increment_column_id(table_start_col, i),
                        "sample_values": [""] * (5),
                    }
                    table["columns"].insert(i, new_column)

            # Case 2: Columns added within or at the end of the table
            elif column_name in [col["id"] for col in table["columns"]]:
                insert_index = next(
                    i
                    for i, col in enumerate(table["columns"])
                    if col["id"] == column_name
                )
                new_end_col = self._increment_column_id(table_end_col, no_of_columns)
                table["range"] = f"{start_col}{start_row}:{new_end_col}{end_row}"
                table["total_columns"] += no_of_columns
                for i in range(no_of_columns):
                    new_column = {
                        "header": f"New Column {i+1}",
                        "id": self._increment_column_id(column_name, i + 1),
                        "sample_values": [""] * 5,
                    }
                    table["columns"].insert(insert_index + i + 1, new_column)

            # Recalculate column IDs
            for i, column in enumerate(table["columns"]):
                column["id"] = self._increment_column_id(table_start_col, i)

        logger.info(f"Added {no_of_columns} column(s) after column {column_name}")
        return sheet_context

    def _remove_column(self, sheet_context: Dict, params: Dict) -> Dict:
        if "column_index" not in params:
            raise ValueError("REMOVE_COLUMN requires 'column_index' in params")

        column_index = params["column_index"]

        for table in sheet_context["tables"]:
            start_col, start_row = self._split_cell_reference(
                table["range"].split(":")[0]
            )
            end_col, end_row = self._split_cell_reference(table["range"].split(":")[1])

            table_start_col = self._column_to_index(start_col)
            table_end_col = self._column_to_index(end_col)

            # Convert column_index to numeric if it's a letter
            if isinstance(column_index, str) and column_index.isalpha():
                column_index = self._column_to_index(column_index)

            # Case 1: Column removed before the table
            if column_index < table_start_col:
                new_start_col = self._index_to_column(table_start_col - 1)
                new_end_col = self._index_to_column(table_end_col - 1)
                table["range"] = f"{new_start_col}{start_row}:{new_end_col}{end_row}"

            # Case 2: Column removed within the table
            elif table_start_col <= column_index <= table_end_col:
                new_end_col = self._index_to_column(table_end_col - 1)
                table["range"] = f"{start_col}{start_row}:{new_end_col}{end_row}"
                table["total_columns"] -= 1
                remove_index = column_index - table_start_col
                table["columns"].pop(remove_index)

            # Case 3: Column removed after the table
            # No action needed for this table

            # Recalculate column IDs
            for i, column in enumerate(table["columns"]):
                column["id"] = self._index_to_column(table_start_col + i)

        logger.info(f"Removed column at index {column_index}")
        return sheet_context

    def _update_cell(self, sheet_context: Dict, params: Dict) -> Dict:
        cell_index = params["cell_index"]
        new_value = params["new_value"]

        column, row = self._split_cell_reference(cell_index)

        for table in sheet_context["tables"]:
            start_col, start_row = self._split_cell_reference(
                table["range"].split(":")[0]
            )
            end_col, end_row = self._split_cell_reference(table["range"].split(":")[1])

            # Check if the cell is in the first row of the table
            if row == start_row and self._is_column_in_range(
                column, start_col, end_col
            ):
                # Find the column in the table and update its header
                for col in table["columns"]:
                    if col["id"] == column:
                        col["header"] = new_value
                        logger.info(
                            f"Updated header in table at range {table['range']}: column {column} to '{new_value}'"
                        )
                        return sheet_context  # Return after updating as a cell should only belong to one table

        logger.info(f"Cell {cell_index} is not a header in any table. No changes made.")
        return sheet_context

    def _add_row(self, sheet_context: Dict, params: Dict) -> Dict:
        if "row_index" not in params or "no_of_rows" not in params:
            raise ValueError("ADD_ROW requires 'row_index' and 'no_of_rows' in params")

        row_index = int(params["row_index"])
        no_of_rows = int(params["no_of_rows"])

        for table in sheet_context["tables"]:
            start_col, start_row = self._split_cell_reference(
                table["range"].split(":")[0]
            )
            end_col, end_row = self._split_cell_reference(table["range"].split(":")[1])

            table_start_row = int(start_row)
            table_end_row = int(end_row)

            # Adjust row_index for 1-based indexing
            adjusted_row_index = max(0, row_index)

            # Case 1: Rows added before the table
            if adjusted_row_index < table_start_row - 1:
                new_start_row = table_start_row + no_of_rows
                new_end_row = table_end_row + no_of_rows
                table["range"] = f"{start_col}{new_start_row}:{end_col}{new_end_row}"

            # Case 2: Rows added at the start of the table
            elif adjusted_row_index == table_start_row - 1:
                new_start_row = table_start_row
                new_end_row = table_end_row + no_of_rows
                table["range"] = f"{start_col}{new_start_row}:{end_col}{new_end_row}"
                table["total_rows"] += no_of_rows

            # Case 3: Rows added within the table
            elif table_start_row - 1 < adjusted_row_index < table_end_row:
                new_end_row = table_end_row + no_of_rows
                table["range"] = f"{start_col}{start_row}:{end_col}{new_end_row}"
                table["total_rows"] += no_of_rows

            # Case 4: Rows added at the end of the table
            elif adjusted_row_index == table_end_row:
                new_end_row = table_end_row + no_of_rows
                table["range"] = f"{start_col}{start_row}:{end_col}{new_end_row}"
                table["total_rows"] += no_of_rows

            # Case 5: Rows added after the table
            # No action needed for this table

        if row_index == 0:
            logger.info(f"Added {no_of_rows} row(s) at the start of the sheet")
        else:
            logger.info(f"Added {no_of_rows} row(s) after row {row_index}")
        return sheet_context

    def _remove_row(self, sheet_context: Dict, params: Dict) -> Dict:
        if "row_index" not in params:
            raise ValueError("REMOVE_ROW requires 'row_index' in params")

        row_index = int(params["row_index"])

        for table in sheet_context["tables"]:
            start_col, start_row = self._split_cell_reference(
                table["range"].split(":")[0]
            )
            end_col, end_row = self._split_cell_reference(table["range"].split(":")[1])

            table_start_row = int(start_row)
            table_end_row = int(end_row)

            # Check if the row being removed is within this table
            if table_start_row <= row_index <= table_end_row:
                # Update the total rows
                table["total_rows"] -= 1

                # Update the range
                new_end_row = table_end_row - 1
                table["range"] = f"{start_col}{start_row}:{end_col}{new_end_row}"

                # Remove value from sample_values for each column
                for column in table["columns"]:
                    remove_index = row_index - table_start_row
                    if 0 <= remove_index < len(column["sample_values"]):
                        column["sample_values"].pop(remove_index)

            # If the row is removed before this table, shift the table range up
            elif row_index < table_start_row:
                new_start_row = table_start_row - 1
                new_end_row = table_end_row - 1
                table["range"] = f"{start_col}{new_start_row}:{end_col}{new_end_row}"

        logger.info(f"Removed row at index {row_index}")
        return sheet_context

    def _get_start_column_id(self, range_str: str) -> str:
        match = re.match(r"([A-Z]+)", range_str)
        return match.group(1) if match else "A"

    def _update_table_range(self, table: Dict) -> None:
        start_cell, _ = table["range"].split(":")
        start_col = self._get_start_column_id(start_cell)
        end_col = self._increment_column_id(start_col, len(table["columns"]) - 1)
        end_row = int(re.search(r"(\d+)$", table["range"]).group(1))
        table["range"] = f"{start_col}{start_cell[len(start_col):]}:{end_col}{end_row}"

    def _split_cell_reference(self, cell_ref: str) -> Tuple[str, str]:
        match = re.match(r"([A-Z]+)(\d+)", cell_ref)
        if match:
            return match.group(1), match.group(2)
        raise ValueError(f"Invalid cell reference: {cell_ref}")

    def _is_column_in_range(self, column: str, start: str, end: str) -> bool:
        return ord(start) <= ord(column) <= ord(end)

    def _column_to_index(self, column: str) -> int:
        return (
            sum((ord(c) - 64) * (26**i) for i, c in enumerate(reversed(column.upper())))
            - 1
        )

    def _index_to_column(self, index: int) -> str:
        if index < 0:
            raise ValueError("Column index must be non-negative")
        column = ""
        index += 1
        while index:
            index, remainder = divmod(index - 1, 26)
            column = chr(65 + remainder) + column
        return column

    def _increment_column_id(self, column_id: str, increment: int) -> str:
        if not column_id:
            return self._index_to_column(
                increment - 1
            )  # Subtract 1 because _index_to_column is 0-based
        current_index = self._column_to_index(column_id)
        return self._index_to_column(current_index + increment)
