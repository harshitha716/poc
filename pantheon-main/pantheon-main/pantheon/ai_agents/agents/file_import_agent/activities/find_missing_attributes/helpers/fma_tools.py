import pandas as pd
import os
import re
from typing import Tuple


def load_file_content(file_path: str) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    correct_path = os.path.join(
        current_dir, "..", "static", os.path.basename(file_path)
    )

    with open(correct_path, "r") as file:
        return file.read()


def parse_region(region: str) -> Tuple[str, int, str, int]:
    match = re.findall(r"([A-Z]+)(\d+):([A-Z]+)(\d+)", region)
    if not match:
        return None
    start_col, start_row, end_col, end_row = match[0]
    return start_col, int(start_row), end_col, int(end_row)


def is_entire_dataframe(
    start_row: int,
    start_col: str,
    end_row: int,
    end_col: str,
    df: pd.DataFrame,
) -> bool:
    start_col_index = column_to_index(start_col)
    end_col_index = column_to_index(end_col)
    return (
        start_row == 0
        and start_col_index == 0
        and end_row >= df.shape[0] - 1
        and end_col_index + 1 >= df.shape[1] - 1
    )


def calculate_remaining_region(
    df: pd.DataFrame,
    start_row: int,
    start_col: str,
    end_row: int,
    end_col: str,
) -> pd.DataFrame:
    start_col_index = column_to_index(start_col)
    end_col_index = column_to_index(end_col)
    full_df_rows, full_df_cols = df.shape

    remaining_top = df.iloc[: start_row - 1, start_col_index : end_col_index + 1]
    remaining_bottom = df.iloc[
        end_row:full_df_rows, start_col_index : end_col_index + 1
    ]
    remaining_left = df.iloc[start_row - 1 : end_row, :start_col_index]
    remaining_right = df.iloc[start_row - 1 : end_row, end_col_index + 1 : full_df_cols]

    return pd.concat([remaining_top, remaining_bottom, remaining_left, remaining_right])


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    # Implement the clean_df function from fileimport_agent.utils.utils
    # This is a placeholder implementation
    return df.dropna(how="all").reset_index(drop=True)


def column_to_index(column: str) -> int:
    index = 0
    for char in column:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1
