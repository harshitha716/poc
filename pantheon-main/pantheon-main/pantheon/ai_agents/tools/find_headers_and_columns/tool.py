import pandas as pd
import re
from typing import List, Dict, Any, Tuple
from dateutil import parser
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)


def increment_column(column: str, times: int) -> str:
    """Increment a column letter by a given number of times."""
    try:
        for _ in range(times):
            if column[-1] < "Z":
                column = column[:-1] + chr(ord(column[-1]) + 1)
            else:
                if len(column) == 1:
                    column = "AA"
                else:
                    column = increment_column(column[:-1], 1) + "A"
        return column
    except Exception as e:
        logger.error(f"Error in increment_column: {str(e)}")
        return column


def is_valid_date_or_time(date_string: str) -> bool:
    """Check if a string is a valid date or time."""
    try:
        parsed_date = parser.parse(date_string, fuzzy=False)
        parsed_date.replace(tzinfo=None)
        formatted_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
        datetime.strptime(formatted_date, "%Y-%m-%d %H:%M:%S")
        return True
    except (ValueError, OverflowError, TypeError):
        return False


def is_number(value: Any) -> bool:
    """Check if a value is a number."""
    cleaned = re.sub(r"[,\s]", "", str(value))
    number_pattern = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
    return bool(number_pattern.match(cleaned))


def get_data_type(value: Any) -> str:
    """Determine the data type of a value."""
    if pd.isna(value):
        return "empty"
    value_str = str(value).strip()
    if is_number(value_str):
        return "number"
    if is_valid_date_or_time(value_str):
        return "date"
    return "string"


def compare_data_types(val1: Any, val2: Any) -> bool:
    """Compare the data types of two values."""
    return get_data_type(val1) == get_data_type(val2)


def find_header_row_and_columns(
    df: pd.DataFrame, max_iterations: int = 100, region: str = "", start_row: int = 0
) -> Tuple[int, List[str], str, int, List[Dict[str, str]], pd.DataFrame]:
    """Find the header row and column information in a DataFrame."""
    try:
        if len(df) < 1:
            return -1, [], region, start_row, [], df

        start_col, end_col, start_row, end_row = parse_region(region)

        rows_to_check = min(end_row - start_row, 3)
        if rows_to_check < 1:
            return -1, [], region, start_row, [], df

        for idx in range(min(len(df) - rows_to_check, max_iterations)):
            potential_header = df.iloc[idx]
            rows_to_compare = [df.iloc[idx + i] for i in range(1, rows_to_check + 1)]

            total_checks = 0
            passed_checks = 0
            column_types = []

            for col in range(len(potential_header)):
                total_checks += 1

                if all(
                    compare_data_types(rows_to_compare[0].iloc[col], row.iloc[col])
                    for row in rows_to_compare[1:]
                ):
                    passed_checks += 1

                # Determine column data type (simplified)
                for row in rows_to_compare:
                    data_type = get_data_type(row.iloc[col])
                    if data_type != "empty":
                        column_types.append(data_type)
                        break
                else:
                    column_types.append(
                        "string"
                    )  # Default to string if all values are empty

            pass_percentage = passed_checks / total_checks if total_checks > 0 else 0

            if pass_percentage >= 0.7:
                header_columns = [
                    str(col).strip() if not pd.isna(col) else "NaN"
                    for col in potential_header
                ]

                new_start_row = start_row + idx

                # Update only the start row in the region
                new_region = f"{start_col}{new_start_row}:{end_col}{end_row}"

                # Identify column region
                column_info = [
                    {
                        "name": name,
                        "type": type,
                        "region": f"{increment_column(start_col, i)}{new_start_row}:{increment_column(start_col, i)}{end_row}",
                    }
                    for i, (name, type) in enumerate(zip(header_columns, column_types))
                ]

                # Update the DataFrame to start from the identified header row
                updated_df = df.iloc[idx:].reset_index(drop=True)
                updated_df.columns = header_columns

                return (
                    idx,
                    header_columns,
                    new_region,
                    new_start_row,
                    column_info,
                    updated_df,
                )

        # If we've gone through all rows without finding a header, return -1 and empty lists
        return -1, [], region, start_row, [], df
    except Exception as e:
        logger.error(f"Error in find_header_row_and_columns: {str(e)}")
        return -1, [], region, start_row, [], df


def parse_region(region: str) -> Tuple[str, str, int, int]:
    """Parse the region string and return start column, end column, start row, and end row."""
    match = re.match(r"([A-Z]+)(\d+):([A-Z]+)(\d+)", region)
    if match:
        return (
            match.group(1),
            match.group(3),
            int(match.group(2)),
            int(match.group(4)),
        )
    return "A", "Z", 1, 1000


# Note: The increment_column function is missing from the original code snippet
# You may need to add it if it's required for the find_header_row_and_columns function
