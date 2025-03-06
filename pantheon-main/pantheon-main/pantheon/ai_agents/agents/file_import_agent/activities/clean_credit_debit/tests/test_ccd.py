import pytest
import pandas as pd
from pantheon.ai_agents.agents.file_import_agent.activities.clean_credit_debit.ccd import (
    clean_credit_debit_activity,
)
from pantheon.ai_agents.agents.file_import_agent.activities.clean_credit_debit.schema.ccd_schema import (
    CleanCreditDebitInput,
    CleanCreditDebitResult,
)


@pytest.fixture
def sample_df():
    dummy_data = {
        "Date": [
            "14 Nov '23",
            "14 Nov '23",
            "13 Nov '23",
            "13 Nov '23",
            "13 Nov '23",
            "12 Nov '23",
            "12 Nov '23",
        ],
        "Transaction Details": [
            "NEERU ENTERPRISES GURGAON IN",
            "PAYTM Noida IN",
            "SMARTSHIFT LOGISTIC Bengaluru IN",
            "UBER INDIA SYSTE PVT LTD NOIDA IN",
            "12356ND07 000000017900 WsVG9VuCrv1",
            "UBER INDIA SYSTE PVT LTD NOIDA IN",
            "SWIGGY INSTAMART BANGALORE IN",
        ],
        "Debit/Credit": [
            "Debit",
            "Credit",
            "Debit",
            "Debit",
            "Debit",
            "Debit",
            "Debit",
        ],
        "Amount (INR)": [
            "₹ 898.00",
            "₹ 1020.00",
            "₹ 100.00",
            "₹ 106.23",
            "₹ 179.00",
            "₹ 41.93",
            "₹ 795.00",
        ],
    }
    return pd.DataFrame(dummy_data)


@pytest.fixture
def sample_column_mapping():
    return [
        {
            "name": "Date",
            "type": "date",
            "region": "A0:A7",
            "mapped_attribute": "initiated_date",
        },
        {
            "name": "Transaction Details",
            "type": "string",
            "region": "B0:B7",
            "mapped_attribute": "transaction_details",
        },
        {
            "name": "Debit/Credit",
            "type": "string",
            "region": "C0:C7",
            "mapped_attribute": "transaction_type",
        },
        {
            "name": "Amount (INR)",
            "type": "string",
            "region": "D0:D7",
            "mapped_attribute": "transaction_amount",
        },
    ]


# @pytest.mark.asyncio
# async def test_clean_credit_debit_activity_success(sample_df, sample_column_mapping):
#     with patch(
#         "pantheon.ai_agents.agents.file_import_agent.activities.clean_credit_debit.helpers.analyze_statement_activity",
#         new_callable=AsyncMock,
#     ) as mock_analyze_statement, patch(
#         "pantheon.ai_agents.agents.file_import_agent.activities.get_regex_patterns.grp.get_regex_patterns_activity",
#         new_callable=AsyncMock,
#     ) as mock_get_regex_patterns:
#         mock_analyze_statement.return_value = {
#             "parameters": {"value_region": "D0:D7", "type_region": "C0:C7"}
#         }
#         mock_get_regex_patterns.return_value.regex_credit = "(?i)^Credit$"
#         mock_get_regex_patterns.return_value.regex_debit = "(?i)^Debit$"

#         input_data = CleanCreditDebitInput(
#             df=sample_df,
#             column_mapping=sample_column_mapping,
#             unmapped_attributes=["credit", "debit", "balance_date"],
#         )

#         result = await clean_credit_debit_activity(input_data)

#         assert isinstance(result, CleanCreditDebitResult)
#         assert isinstance(result.cb, RegexConfig)
#         assert result.cb.amount_column_region == "D0:D7"
#         assert result.cb.type_region == "C0:C7"
#         assert result.cb.regex_credit == "(?i)^Credit$"
#         assert result.cb.regex_debit == "(?i)^Debit$"
#         assert result.unmapped_attributes == ["balance_date"]


@pytest.mark.asyncio
async def test_clean_credit_debit_activity_no_credit_debit(
    sample_df, sample_column_mapping
):
    input_data = CleanCreditDebitInput(
        df=sample_df,
        column_mapping=sample_column_mapping,
        unmapped_attributes=["balance_date"],
    )

    result = await clean_credit_debit_activity(input_data)

    assert isinstance(result, CleanCreditDebitResult)
    assert result.cb == {}
    assert result.unmapped_attributes == ["balance_date"]


# @pytest.mark.asyncio
# async def test_clean_credit_debit_activity_exception(sample_df, sample_column_mapping):
#     with patch(
#         "pantheon.ai_agents.agents.file_import_agent.activities.analyze_statement.ans.analyze_statement_activity",
#         new_callable=AsyncMock,
#     ) as mock_analyze_statement:
#         mock_analyze_statement.side_effect = Exception("Test exception")

#         input_data = CleanCreditDebitInput(
#             df=sample_df,
#             column_mapping=sample_column_mapping,
#             unmapped_attributes=["credit", "debit", "balance_date"],
#         )

#         result = await clean_credit_debit_activity(input_data)

#         assert isinstance(result, CleanCreditDebitResult)
#         assert isinstance(result.cb, RegexConfig)
#         assert result.cb.amount_column_region == "D0:D7"
#         assert result.cb.type_region == "C0:C7"
#         assert result.cb.regex_credit == "(?i)^Credit$"
#         assert result.cb.regex_debit == "(?i)^Debit$"
#         assert result.unmapped_attributes == ["balance_date"]


@pytest.mark.asyncio
async def test_clean_credit_debit_activity_missing_transaction_amount(
    sample_df, sample_column_mapping
):
    invalid_column_mapping = [
        item
        for item in sample_column_mapping
        if item["mapped_attribute"] != "transaction_amount"
    ]

    input_data = CleanCreditDebitInput(
        df=sample_df,
        column_mapping=invalid_column_mapping,
        unmapped_attributes=["credit", "debit", "balance_date"],
    )

    result = await clean_credit_debit_activity(input_data)
    assert isinstance(result, CleanCreditDebitResult)
    assert result.cb == {}
    assert result.unmapped_attributes == ["credit", "debit", "balance_date"]


# pytest --cov=pantheon.ai_agents.agents.file_import_agent.activities.clean_credit_debit --cov-report=term-missing
