import pytest
import pandas as pd
from pantheon.ai_agents.tools.detect_island_and_clean.tool import (
    col_num_to_letter,
    detect_largest_island,
    clean_dataframe,
    update_region,
    split_column_row,
    increment_column,
)


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame(
        {
            0: [1, 2, 3, None, 5],
            1: [None, 2, 3, 4, 5],
            2: [1, 2, None, 4, 5],
            3: [None, None, None, None, None],
        }
    )


def test_col_num_to_letter():
    assert col_num_to_letter(1) == "A"
    assert col_num_to_letter(26) == "Z"
    assert col_num_to_letter(27) == "AA"
    assert col_num_to_letter(0) == ""


def test_detect_largest_island(sample_dataframe):
    region, island_df = detect_largest_island(sample_dataframe)
    assert region == "A1:C5"
    assert island_df.shape == (5, 3)


def test_detect_largest_island_with_start_row(sample_dataframe):
    region, island_df = detect_largest_island(sample_dataframe, start_row=2)
    assert region == "A2:C5"
    assert island_df.shape == (4, 3)


def test_clean_dataframe(sample_dataframe):
    cleaned_df, updated_region = clean_dataframe(sample_dataframe, "A1:D5")
    assert cleaned_df.shape == (5, 3)
    assert updated_region == "A1:C5"


def test_update_region():
    assert update_region("A1:D5", 3, 0, 2) == "A1:C5"
    assert update_region("B2:E6", 3, 1, 3) == "C2:E6"


def test_update_region_error():
    assert update_region("A1D5", None, None, 3) == ""
    assert update_region("B2E6", 3, None, 3) == ""


def test_split_column_row():
    assert split_column_row("A1") == ("A", "1")
    assert split_column_row("AB23") == ("AB", "23")


def test_split_column_row_error():
    assert split_column_row(None) == ("", "")
    assert split_column_row(3123) == ("", "")


def test_increment_column():
    assert increment_column("A", 1) == "B"
    assert increment_column("Z", 1) == "AA"
    assert increment_column("AA", 1) == "AB"


def test_increment_column_error():
    assert increment_column(312, 1) == 312
    assert increment_column(None, 1) is None


def test_detect_largest_island_empty_dataframe():
    region, island_df = detect_largest_island(233)
    assert region == ""
    assert island_df.empty


def test_clean_dataframe_empty():
    empty_df = pd.DataFrame()
    cleaned_df, updated_region = clean_dataframe(empty_df, "A1:A1")
    assert cleaned_df.empty
    assert updated_region == "A1:A1"


def test_clean_dataframe_invalid_threshold():
    df = pd.DataFrame({0: [1, 2, 3]})
    cleaned_df, updated_region = clean_dataframe(df, "A1:A3", threshold=1.1)
    assert cleaned_df.shape == (3, 1)
    assert updated_region == "A1:A3"


def test_col_num_to_letter_invalid():
    assert col_num_to_letter(-1) == ""


# pytest pantheon/ai_agents/tools/detect_island_and_clean/tests/test_tool_dic.py --cov=pantheon.ai_agents.tools.detect_island_and_clean --cov-report=term-missing
