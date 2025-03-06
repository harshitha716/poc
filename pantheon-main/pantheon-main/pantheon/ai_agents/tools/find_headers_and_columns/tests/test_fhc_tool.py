import pytest
import pandas as pd
from pantheon.ai_agents.tools.find_headers_and_columns.tool import (
    increment_column,
    is_valid_date_or_time,
    is_number,
    get_data_type,
    compare_data_types,
    find_header_row_and_columns,
    parse_region,
)


def test_increment_column():
    assert increment_column("A", 1) == "B"
    assert increment_column("Z", 1) == "AA"
    assert increment_column("AA", 1) == "AB"
    assert increment_column("AZ", 1) == "BA"


def test_is_valid_date_or_time():
    assert is_valid_date_or_time("2023-05-01")
    assert is_valid_date_or_time("14:30:00")
    assert is_valid_date_or_time("2023-05-01 14:30:00")
    assert not is_valid_date_or_time("not a date")


def test_is_number():
    assert is_number("123")
    assert is_number("-123.45")
    assert is_number("1.23e-4")
    assert not is_number("abc")
    assert not is_number(["1"])


def test_get_data_type():
    assert get_data_type("123") == "number"
    assert get_data_type("2023-05-01") == "date"
    assert get_data_type("abc") == "string"
    assert get_data_type(pd.NA) == "empty"
    assert get_data_type(["2"]) == "string"


def test_compare_data_types():
    assert compare_data_types("123", "456")
    assert compare_data_types("2023-05-01", "2023-06-01")
    assert not compare_data_types("123", "abc")


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            0: ["Date", "2023-05-01", "2023-05-02", "2023-05-03"],
            1: ["Value", 100, 200, 300],
            2: ["Category", "A", "B", "C"],
        }
    )


def test_find_header_row_and_columns(sample_df):
    result = find_header_row_and_columns(sample_df, region="A1:C4")
    assert result[0] == 0  # header_row_index
    assert result[1] == ["Date", "Value", "Category"]  # header_columns
    assert result[2] == "A1:C4"  # new_region
    assert result[3] == 1  # new_start_row
    assert len(result[4]) == 3  # column_info
    assert result[5].shape == (4, 3)  # updated_df


def test_find_header_row_and_columns_no_header():
    result = find_header_row_and_columns(123, region="A1:C4")
    assert result[0] == -1  # header_row_index
    assert result[1] == []  # header_columns


def test_parse_region():
    assert parse_region("A1:C4") == ("A", "C", 1, 4)
    assert parse_region("invalid") == ("A", "Z", 1, 1000)


def test_error_handling():
    assert increment_column(None, 1) is None
    assert get_data_type(None) == "empty"


# pytest pantheon/ai_agents/tools/find_headers_and_columns/tests/test_fhc_tool.py --cov=pantheon.ai_agents.tools.find_headers_and_columns --cov-report=term-missing
