import pytest
import pandas as pd
from pantheon.ai_agents.agents.file_import_agent.activities.find_header_and_columns.fhc import (
    find_header_and_columns,
)
from pantheon.ai_agents.agents.file_import_agent.activities.find_header_and_columns.schema.fhc_schema import (
    FindHeaderAndColumnsInput,
    FindHeaderAndColumnsOutput,
    ColumnInfo,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            0: ["Date", "2023-05-01", "2023-05-02", "2023-05-03"],
            1: ["Value", 100, 200, 300],
            2: ["Category", "A", "B", "C"],
        }
    )


def test_find_header_and_columns(sample_df):
    input_data = FindHeaderAndColumnsInput(
        island_df=sample_df, region="A1:C4", start_row=1
    )

    result = find_header_and_columns(input_data)

    assert isinstance(result, FindHeaderAndColumnsOutput)
    assert result.header_row_index == 0
    assert result.header_columns == ["Date", "Value", "Category"]
    assert result.new_region == "A1:C4"
    assert result.new_start_row == 1
    assert len(result.column_info) == 3
    assert isinstance(result.column_info[0], ColumnInfo)
    assert result.updated_df.shape == (4, 3)


def test_find_header_and_columns_no_header(sample_df):
    df_no_header = pd.DataFrame(sample_df.values)
    input_data = FindHeaderAndColumnsInput(
        island_df=df_no_header, region="A1:C4", start_row=1
    )

    result = find_header_and_columns(input_data)

    assert isinstance(result, FindHeaderAndColumnsOutput)
    assert result.header_row_index == 0
    assert result.header_columns == ["Date", "Value", "Category"]
    assert result.new_region == "A1:C4"
    assert result.new_start_row == 1
    assert len(result.column_info) == 3


# pytest pantheon/ai_agents/agents/file_import_agent/activities/find_header_and_columns/tests/test_fhc.py --cov=pantheon.ai_agents.agents.file_import_agent.activities.find_header_and_columns --cov-report=term-missing
