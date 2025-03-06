import pandas as pd
from typing import Tuple

import structlog

logger = structlog.get_logger(__name__)


def col_num_to_letter(col_num: int) -> str:
    """Convert a column number to an Excel-style column letter."""
    try:
        if col_num < 1:
            raise ValueError("Column number must be 1 or greater")
        col_num -= 1
        letters = []
        while col_num >= 0:
            letters.append(chr(65 + (col_num % 26)))
            col_num = (col_num // 26) - 1
        return "".join(reversed(letters))
    except Exception as e:
        logger.error(f"Error in col_num_to_letter: {str(e)}")
        return ""


def detect_largest_island(
    df: pd.DataFrame, start_row: int = 0
) -> Tuple[str, pd.DataFrame, int]:
    """Detect the largest contiguous non-empty region (island) in a DataFrame."""
    try:
        start_row = max(0, start_row - 1)
        df_slice = df.iloc[start_row:]

        empty_rows = df_slice.isna().all(axis=1)
        empty_row_indices = empty_rows[empty_rows].index.tolist()

        if not empty_row_indices:
            empty_row_indices = [len(df_slice)]

        largest_island_size = 0
        largest_island_region = ""
        largest_island_df = None

        island_start = 0
        for end_row in empty_row_indices:
            if end_row > island_start:
                island_slice = df_slice.iloc[island_start:end_row]
                non_empty_cols = island_slice.notna().any()

                if non_empty_cols.any():
                    non_empty_col_indices = non_empty_cols[non_empty_cols].index
                    start_col = non_empty_col_indices[0]
                    end_col = non_empty_col_indices[-1]

                    island_size = (end_row - island_start) * (end_col - start_col + 1)

                    if island_size > largest_island_size:
                        largest_island_size = island_size
                        largest_island_region = f"{col_num_to_letter(start_col + 1)}{start_row + island_start + 1}:{col_num_to_letter(end_col + 1)}{start_row + end_row}"
                        largest_island_df = island_slice.iloc[
                            :, start_col : end_col + 1
                        ]

            island_start = end_row + 1 - start_row

        return largest_island_region, largest_island_df
    except Exception as e:
        logger.error(f"Error in detect_largest_island: {str(e)}")
        return "", pd.DataFrame()


def clean_dataframe(
    df: pd.DataFrame, region: str, threshold: float = 0.1
) -> Tuple[pd.DataFrame, str]:
    """Clean dataframe to remove columns that are not meeting the threshold."""
    try:
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")

        def column_meets_threshold(column):
            return column.notna().sum() / len(column) >= threshold

        start_col = 0
        while start_col < df.shape[1] and not column_meets_threshold(
            df.iloc[:, start_col]
        ):
            start_col += 1

        end_col = df.shape[1] - 1
        while end_col > start_col and not column_meets_threshold(df.iloc[:, end_col]):
            end_col -= 1

        # Slice the DataFrame to keep only the columns between start_col and end_col (inclusive)
        cleaned_df = df.iloc[:, start_col : end_col + 1]

        # Update the region based on the new DataFrame shape
        if cleaned_df.shape != df.shape:
            updated_region = update_region(
                region, cleaned_df.shape[1], start_col, end_col
            )
        else:
            updated_region = region

        return cleaned_df, updated_region
    except Exception as e:
        logger.error(f"Error in clean_dataframe: {str(e)}")
        return df, region


def update_region(region: str, new_columns: int, start_col: int, end_col: int) -> str:
    """Update the region based on new DataFrame shape."""
    try:
        start, end = region.split(":")
        start_col_letter, start_row = split_column_row(start)
        end_col_letter, end_row = split_column_row(end)

        # Calculate the correct start and end columns
        new_start_col = increment_column(start_col_letter, start_col)
        new_end_col = increment_column(start_col_letter, end_col)

        return f"{new_start_col}{start_row}:{new_end_col}{end_row}"
    except Exception as e:
        logger.error(f"Error in update_region: {str(e)}")
        return ""


def split_column_row(cell: str) -> Tuple[str, str]:
    """Split a cell reference into column and row parts."""
    try:
        for i, char in enumerate(cell):
            if char.isdigit():
                return cell[:i], cell[i:]
        return cell, ""
    except Exception as e:
        logger.error(f"Error in split_column_row: {str(e)}")
        return "", ""


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
