import pytest
import pandas as pd
from pantheon_v2.tools.common.pandas.helpers.add_metadata_columns import (
    process_metadata_value,
    create_metadata_columns,
    add_metadata_to_df,
)


def test_process_metadata_value():
    """Test processing of metadata values for both array and non-array inputs"""
    # Test list input
    list_value = ["a", "b", "c"]
    assert process_metadata_value(list_value) == list_value

    # Test string input
    string_value = "test"
    assert process_metadata_value(string_value) == "test"

    # Test numeric input
    numeric_value = 123
    assert process_metadata_value(numeric_value) == 123


def test_create_metadata_columns():
    """Test creation of metadata columns DataFrame"""
    # Test with mixed metadata types
    metadata = {"single_value": "test", "array_value": ["a", "b", "c"], "numeric": 123}
    df_length = 3

    result = create_metadata_columns(metadata, df_length)

    # Get the header row (first row) values
    header_values = result.iloc[0].tolist()

    # Check that header contains expected column names
    assert "single_value" in header_values
    assert "array_value_1" in header_values
    assert "array_value_2" in header_values
    assert "array_value_3" in header_values
    assert "numeric" in header_values

    # Get indices for each column from header row
    single_value_idx = header_values.index("single_value")
    array_value_1_idx = header_values.index("array_value_1")
    numeric_idx = header_values.index("numeric")

    # Check data rows using numeric indices
    assert result.iloc[1][single_value_idx] == "test"
    assert result.iloc[1][array_value_1_idx] == "a"
    assert result.iloc[1][numeric_idx] == 123

    # Check DataFrame dimensions
    assert len(result) == df_length + 1  # +1 for header row
    assert (
        len(result.columns) == 5
    )  # 3 columns from array_value + single_value + numeric


def test_add_metadata_to_df():
    """Test adding metadata to existing DataFrame"""
    # Create sample source DataFrame
    source_data = {"col1": ["A", "B", "C"], "col2": [1, 2, 3]}
    df = pd.DataFrame(source_data)

    # Create metadata
    metadata = {"source": "test_source", "tags": ["tag1", "tag2"]}

    result = add_metadata_to_df(df, metadata)

    # Check original columns preserved
    assert "col1" in result.columns
    assert "col2" in result.columns

    # Check metadata columns added
    assert "source" in result.columns
    assert "tags_1" in result.columns
    assert "tags_2" in result.columns

    # Check values
    assert result["source"].iloc[0] == "test_source"
    assert result["tags_1"].iloc[0] == "tag1"
    assert result["tags_2"].iloc[0] == "tag2"


def test_add_metadata_to_df_with_numeric_headers():
    """Test adding metadata to DataFrame with numeric headers"""
    # Create DataFrame with numeric headers
    df = pd.DataFrame(
        {0: ["Header1", "Value1", "Value2"], 1: ["Header2", "Value3", "Value4"]}
    )

    metadata = {"source": "test_source"}

    result = add_metadata_to_df(df, metadata)

    # Check headers were properly handled
    assert "Header1" in result.columns
    assert "Header2" in result.columns
    assert "source" in result.columns

    # Check values
    assert result["Header1"].iloc[0] == "Value1"
    assert result["source"].iloc[0] == "test_source"


if __name__ == "__main__":
    pytest.main()
