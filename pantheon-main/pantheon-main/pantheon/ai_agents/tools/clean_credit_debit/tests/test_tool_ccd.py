import pytest
import pandas as pd
from pantheon.ai_agents.tools.clean_credit_debit.tool import (
    excel_col_to_index,
    group_csv_column,
    group_field_amount_patterns,
    AmountPattern,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "Description": ["Purchase", "Deposit", "Withdrawal"],
            "Type": ["Debit", "Credit", "Debit"],
            "Amount": ["$100.00", "$200.00", "$150.00"],
        }
    )


def test_excel_col_to_index():
    assert excel_col_to_index("A") == 0
    assert excel_col_to_index("Z") == 25
    assert excel_col_to_index("AA") == 26
    assert excel_col_to_index("AB") == 27


def test_group_csv_column(sample_df):
    result = group_csv_column(sample_df, "C1:C4")
    assert set(result) == {"Debit", "Credit"}


def test_group_csv_column_invalid_range(sample_df):
    with pytest.raises(ValueError):
        group_csv_column(sample_df, "A1:B4")


def test_group_field_amount_patterns(sample_df):
    result = group_field_amount_patterns(sample_df, "D1:D4")
    assert len(result) == 1
    assert isinstance(result[0], AmountPattern)
    assert result[0].pattern == "$"


def test_group_field_amount_patterns_with_negative():
    df = pd.DataFrame({"Amount": ["$100.00", "-$200.00", "$300.00"]})
    result = group_field_amount_patterns(df, "A1:A4")
    assert len(result) == 2
    patterns = {r.pattern for r in result}
    assert patterns == {"$", "-$"}


def test_group_field_amount_patterns_invalid_range(sample_df):
    with pytest.raises(ValueError):
        group_field_amount_patterns(sample_df, "A1:B4")


# pytest --cov=pantheon.ai_agents.tools.clean_credit_debit.tool --cov-report=term-missing pantheon/ai_agents/tools/clean_credit_debit/tests/test_tool_ccd.py
