import re
import pandas as pd
import random
from pydantic import BaseModel
from typing import List


class AmountPattern(BaseModel):
    pattern: str
    example_value: str


def excel_col_to_index(col_str):
    """Convert Excel column letter to column index"""
    exp = 0
    col = 0
    for char in reversed(col_str.upper()):
        col += (ord(char) - ord("A") + 1) * (26**exp)
        exp += 1
    return col - 1  # zero-based index


def group_csv_column(df: pd.DataFrame, column_range: str) -> List[str]:
    start_cell, end_cell = column_range.split(":")
    start_col = re.match(r"([A-Z]+)", start_cell).group(1)
    end_col = re.match(r"([A-Z]+)", end_cell).group(1)
    start_row = int(re.search(r"(\d+)", start_cell).group(1)) - 1  # zero-based index
    end_row = int(re.search(r"(\d+)", end_cell).group(1)) - 1  # zero-based index

    start_row += 1

    col_index = excel_col_to_index(start_col)

    if start_col != end_col:
        raise ValueError("The range must be in a single column")

    # Get the column name based on the index
    column_name = df.columns[col_index]

    # Extract the unique values from the specified range
    unique_values = df.iloc[start_row : end_row + 1][column_name].unique()

    # Convert to a regular Python list and remove any NaN values
    return list(unique_values[pd.notna(unique_values)])


def group_field_amount_patterns(
    df: pd.DataFrame, column_range: str
) -> List[AmountPattern]:
    start_cell, end_cell = column_range.split(":")
    start_col = re.match(r"([A-Z]+)", start_cell).group(1)
    end_col = re.match(r"([A-Z]+)", end_cell).group(1)
    start_row = int(re.search(r"(\d+)", start_cell).group(1)) - 1  # zero-based index
    end_row = int(re.search(r"(\d+)", end_cell).group(1)) - 1  # zero-based index
    start_row += 1  # Adjust for header row

    col_index = excel_col_to_index(start_col)

    if start_col != end_col:
        raise ValueError("The range must be in a single column")

    # Get the column name based on the index
    column_name = df.columns[col_index]

    def extract_pattern(value):
        # Convert to string if not already
        value = str(value)
        # Check if the value starts with a minus sign
        starts_with_minus = value.startswith("-")
        # Remove all digits, decimal points, and whitespace
        pattern = re.sub(r"[\d\.\s]", "", value)
        # If the original value started with a minus and it's not in the pattern, add it back
        if starts_with_minus and not pattern.startswith("-"):
            pattern = "-" + pattern
        # Trim the result
        return pattern.strip()

    # Extract the specified column range
    column = df.iloc[start_row : end_row + 1][column_name]

    # Extract patterns
    patterns = column.apply(extract_pattern)

    # Group by patterns
    grouped = patterns.groupby(patterns)

    # Create the result array
    result: List[AmountPattern] = []
    for pattern, group in grouped:
        example_value = random.choice(group.index.tolist())
        result.append(
            AmountPattern(
                pattern=pattern, example_value=str(df.loc[example_value, column_name])
            )
        )

    return result
