import pytest
import pandas as pd
from unittest.mock import AsyncMock, patch
from pantheon.ai_agents.agents.file_import_agent.activities.column_mapping.cm import (
    column_mapping_activity,
)
from pantheon.ai_agents.agents.file_import_agent.activities.column_mapping.schema.cm_schema import (
    ColumnInfo,
    ColumnMappingResult,
)
from pantheon.ai_agents.agents.file_import_agent.activities.column_mapping.helpers.cm_handle_dates import (
    extract_from_region,
)


@pytest.fixture
def mock_data():
    return {
        "Post Date": [
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
        "Value Date": [
            "14 Nov '23",
            "14 Nov '23",
            "13 Nov '23",
            "13 Nov '23",
            "13 Nov '23",
            "12 Nov '23",
            "12 Nov '23",
        ],
    }


@pytest.fixture
def mock_column_info():
    return [
        ColumnInfo(name="Post Date", type="date", region="A6:A7"),
        ColumnInfo(name="Transaction Details", type="string", region="B6:B7"),
        ColumnInfo(name="Debit/Credit", type="string", region="C6:C7"),
        ColumnInfo(name="Amount (INR)", type="string", region="D6:D7"),
        ColumnInfo(name="Value Date", type="date", region="E6:E7"),
    ]


@pytest.fixture
def mock_llm_response():
    return """
{
  "mapped_columns": [
    {
      "name": "Post Date",
      "type": "date",
      "region": "A6:A7",
      "mapped_attribute": "initiated_date",
      "attribute_type": "date"
    },
    {
      "name": "Transaction Details",
      "type": "string",
      "region": "B6:B7",
      "mapped_attribute": "remarks",
      "attribute_type": "string"
    },
    {
      "name": "Debit/Credit",
      "type": "string",
      "region": "C6:C7",
      "mapped_attribute": "transaction_type",
      "attribute_type": "string"
    },
    {
      "name": "Amount (INR)",
      "type": "string",
      "region": "D6:D7",
      "mapped_attribute": "transaction_amount",
      "attribute_type": "float"
    },
    {
      "name": "Value Date",
      "type": "date",
      "region": "E6:E7",
      "mapped_attribute": "updated_date",
      "attribute_type": "date"
    }
  ],
  "unmapped_attributes": [
    "closing_balance_updated_date",
    "account_number",
    "credit",
    "debit",
    "balance",
    "currency_code",
    "status",
    "transaction_sub_type",
    "bank_reference_id",
    "tag"
  ],
  "errors": [
    "Unable to identify columns for several required attributes including account_number, balance, and updated_date.",
    "The 'Amount (INR)' column contains both credits and debits, so it's mapped to transaction_amount instead of separate credit and debit fields."
  ]
}
"""


@pytest.mark.asyncio
async def test_column_mapping_activity(mock_data, mock_column_info, mock_llm_response):
    df = pd.DataFrame(mock_data)
    original_df = pd.DataFrame(mock_data)

    with patch(
        "pantheon.ai_agents.agents.file_import_agent.activities.column_mapping.helpers.cm_helper.LLMService"
    ) as MockLLMService:
        mock_llm_instance = MockLLMService.return_value
        mock_llm_instance.send_message_async = AsyncMock()
        mock_llm_instance.send_message_async.return_value.content = mock_llm_response

        result = await column_mapping_activity(df, mock_column_info, original_df)

        assert isinstance(result, ColumnMappingResult)
        assert len(result.mapped_columns) == 6
        assert len(result.unmapped_attributes) == 9
        assert len(result.errors) == 2

        # Check specific mappings
        assert result.mapped_columns[0]["mapped_attribute"] == "initiated_date"
        assert result.mapped_columns[1]["mapped_attribute"] == "remarks"
        assert result.mapped_columns[2]["mapped_attribute"] == "transaction_type"
        assert result.mapped_columns[3]["mapped_attribute"] == "transaction_amount"

        # Check specific unmapped attributes
        assert "credit" in result.unmapped_attributes
        assert "debit" in result.unmapped_attributes

        # Check specific errors
        assert any(
            "Unable to identify columns for several required attributes" in error
            for error in result.errors
        )
        assert any(
            "The 'Amount (INR)' column contains both credits and debits" in error
            for error in result.errors
        )

        # Verify LLM service call
        mock_llm_instance.send_message_async.assert_called_once()
        call_args = mock_llm_instance.send_message_async.call_args[1]
        assert "messages" in call_args
        assert call_args["model"] == "claude-3-5-sonnet-20240620"


@pytest.mark.asyncio
async def test_column_mapping_activity_error_handling(mock_data, mock_column_info):
    df = pd.DataFrame(mock_data)
    original_df = pd.DataFrame(mock_data)

    with patch(
        "pantheon.ai_agents.agents.file_import_agent.activities.column_mapping.helpers.cm_helper.LLMService"
    ) as MockLLMService:
        mock_llm_instance = MockLLMService.return_value
        mock_llm_instance.send_message_async = AsyncMock(
            side_effect=Exception("LLM service error")
        )

        result = await column_mapping_activity(df, mock_column_info, original_df)

        assert isinstance(result, ColumnMappingResult)
        assert len(result.mapped_columns) == 0
        assert len(result.unmapped_attributes) == 0
        assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_column_mapping_activity_invalid_response(mock_data, mock_column_info):
    df = pd.DataFrame(mock_data)
    original_df = pd.DataFrame(mock_data)

    with patch(
        "pantheon.ai_agents.agents.file_import_agent.activities.column_mapping.helpers.cm_helper.LLMService"
    ) as MockLLMService:
        mock_llm_instance = MockLLMService.return_value
        mock_llm_instance.send_message_async = AsyncMock()
        mock_llm_instance.send_message_async.return_value.content = "Invalid JSON"

        result = await column_mapping_activity(df, mock_column_info, original_df)

        assert isinstance(result, ColumnMappingResult)
        assert len(result.mapped_columns) == 0
        assert len(result.unmapped_attributes) == 0
        assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_column_mapping_activity_empty_dataframe(
    mock_column_info, mock_llm_response
):
    df = pd.DataFrame()
    original_df = pd.DataFrame()

    with patch(
        "pantheon.ai_agents.agents.file_import_agent.activities.column_mapping.helpers.cm_helper.LLMService"
    ) as MockLLMService:
        mock_llm_instance = MockLLMService.return_value
        mock_llm_instance.send_message_async = AsyncMock()
        mock_llm_instance.send_message_async.return_value.content = mock_llm_response

        result = await column_mapping_activity(df, mock_column_info, original_df)

        assert isinstance(result, ColumnMappingResult)
        assert len(result.mapped_columns) == 3
        assert len(result.unmapped_attributes) == 12
        assert len(result.errors) == 2


@pytest.mark.asyncio
async def test_column_mapping_activity_empty_column_info(mock_data, mock_llm_response):
    df = pd.DataFrame(mock_data)
    original_df = pd.DataFrame(mock_data)

    with patch(
        "pantheon.ai_agents.agents.file_import_agent.activities.column_mapping.helpers.cm_helper.LLMService"
    ) as MockLLMService:
        mock_llm_instance = MockLLMService.return_value
        mock_llm_instance.send_message_async = AsyncMock()
        mock_llm_instance.send_message_async.return_value.content = mock_llm_response

        result = await column_mapping_activity(df, [], original_df)

        assert isinstance(result, ColumnMappingResult)
        assert len(result.mapped_columns) == 6
        assert len(result.unmapped_attributes) == 9
        assert len(result.errors) == 2


@pytest.fixture
def mock_data_alt():
    return {
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
        "Transaction Date": [
            "14 Nov '23",
            "14 Nov '23",
            "13 Nov '23",
            "13 Nov '23",
            "13 Nov '23",
            "12 Nov '23",
            "12 Nov '23",
        ],
    }


@pytest.fixture
def mock_column_info_alt():
    return [
        ColumnInfo(name="Date", type="date", region="A6:A7"),
        ColumnInfo(name="Transaction Details", type="string", region="B6:B7"),
        ColumnInfo(name="Debit/Credit", type="string", region="C6:C7"),
        ColumnInfo(name="Amount (INR)", type="string", region="D6:D7"),
        ColumnInfo(name="Transaction Date", type="date", region="E6:E7"),
    ]


@pytest.fixture
def mock_llm_response_alt():
    return """
{
  "mapped_columns": [
    {
      "name": "Date",
      "type": "date",
      "region": "A6:A7",
      "mapped_attribute": "initiated_date",
      "attribute_type": "date"
    },
    {
      "name": "Transaction Details",
      "type": "string",
      "region": "B6:B7",
      "mapped_attribute": "remarks",
      "attribute_type": "string"
    },
    {
      "name": "Debit/Credit",
      "type": "string",
      "region": "C6:C7",
      "mapped_attribute": "transaction_type",
      "attribute_type": "string"
    },
    {
      "name": "Amount (INR)",
      "type": "string",
      "region": "D6:D7",
      "mapped_attribute": "transaction_amount",
      "attribute_type": "float"
    },
    {
      "name": "Transaction Date",
      "type": "date",
      "region": "E6:E7",
      "mapped_attribute": "updated_date",
      "attribute_type": "date"
    }
  ],
  "unmapped_attributes": [
    "closing_balance_updated_date",
    "account_number",
    "credit",
    "debit",
    "balance",
    "currency_code",
    "status",
    "transaction_sub_type",
    "bank_reference_id",
    "tag"
  ],
  "errors": [
    "Unable to identify columns for several required attributes including account_number, balance, and updated_date.",
    "The 'Amount (INR)' column contains both credits and debits, so it's mapped to transaction_amount instead of separate credit and debit fields."
  ]
}
"""


@pytest.mark.asyncio
async def test_column_mapping_activity_alt(
    mock_data_alt, mock_column_info_alt, mock_llm_response_alt
):
    df = pd.DataFrame(mock_data_alt)
    original_df = pd.DataFrame(mock_data_alt)

    with patch(
        "pantheon.ai_agents.agents.file_import_agent.activities.column_mapping.helpers.cm_helper.LLMService"
    ) as MockLLMService:
        mock_llm_instance = MockLLMService.return_value
        mock_llm_instance.send_message_async = AsyncMock()
        mock_llm_instance.send_message_async.return_value.content = (
            mock_llm_response_alt
        )

        result = await column_mapping_activity(df, mock_column_info_alt, original_df)

        assert isinstance(result, ColumnMappingResult)
        assert len(result.mapped_columns) == 6
        assert len(result.unmapped_attributes) == 9
        assert len(result.errors) == 2

        # Check specific mappings
        assert result.mapped_columns[0]["mapped_attribute"] == "initiated_date"
        assert result.mapped_columns[1]["mapped_attribute"] == "remarks"
        assert result.mapped_columns[2]["mapped_attribute"] == "transaction_type"
        assert result.mapped_columns[3]["mapped_attribute"] == "transaction_amount"

        # Check specific unmapped attributes
        assert "credit" in result.unmapped_attributes
        assert "debit" in result.unmapped_attributes

        # Verify LLM service call
        mock_llm_instance.send_message_async.assert_called_once()
        call_args = mock_llm_instance.send_message_async.call_args[1]
        assert "messages" in call_args
        assert call_args["model"] == "claude-3-5-sonnet-20240620"


@pytest.fixture
def mock_data_no_value_date():
    return {
        "Post Date": [
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


@pytest.fixture
def mock_column_info_no_value_date():
    return [
        ColumnInfo(name="Post Date", type="date", region="A6:A7"),
        ColumnInfo(name="Transaction Details", type="string", region="B6:B7"),
        ColumnInfo(name="Debit/Credit", type="string", region="C6:C7"),
        ColumnInfo(name="Amount (INR)", type="string", region="D6:D7"),
    ]


@pytest.fixture
def mock_llm_response_no_value_date():
    return """
{
  "mapped_columns": [
    {
      "name": "Post Date",
      "type": "date",
      "region": "A6:A7",
      "mapped_attribute": "initiated_date",
      "attribute_type": "date"
    },
    {
      "name": "Transaction Details",
      "type": "string",
      "region": "B6:B7",
      "mapped_attribute": "remarks",
      "attribute_type": "string"
    },
    {
      "name": "Debit/Credit",
      "type": "string",
      "region": "C6:C7",
      "mapped_attribute": "transaction_type",
      "attribute_type": "string"
    },
    {
      "name": "Amount (INR)",
      "type": "string",
      "region": "D6:D7",
      "mapped_attribute": "transaction_amount",
      "attribute_type": "float"
    }
  ],
  "unmapped_attributes": [
    "closing_balance_updated_date",
    "account_number",
    "credit",
    "debit",
    "balance",
    "currency_code",
    "status",
    "transaction_sub_type",
    "bank_reference_id",
    "tag",
    "updated_date"
  ],
  "errors": [
    "Unable to identify columns for several required attributes including account_number, balance, and updated_date.",
    "The 'Amount (INR)' column contains both credits and debits, so it's mapped to transaction_amount instead of separate credit and debit fields.",
    "Missing 'Value Date' column which is typically used for updated_date."
  ]
}
"""


@pytest.mark.asyncio
async def test_column_mapping_activity_no_value_date(
    mock_data_no_value_date,
    mock_column_info_no_value_date,
    mock_llm_response_no_value_date,
):
    df = pd.DataFrame(mock_data_no_value_date)
    original_df = pd.DataFrame(mock_data_no_value_date)

    with patch(
        "pantheon.ai_agents.agents.file_import_agent.activities.column_mapping.helpers.cm_helper.LLMService"
    ) as MockLLMService:
        mock_llm_instance = MockLLMService.return_value
        mock_llm_instance.send_message_async = AsyncMock()
        mock_llm_instance.send_message_async.return_value.content = (
            mock_llm_response_no_value_date
        )

        result = await column_mapping_activity(
            df, mock_column_info_no_value_date, original_df
        )

        assert isinstance(result, ColumnMappingResult)
        assert len(result.mapped_columns) == 6
        assert len(result.unmapped_attributes) == 9
        assert len(result.errors) == 3

        # Check specific mappings
        assert result.mapped_columns[0]["mapped_attribute"] == "initiated_date"
        assert result.mapped_columns[1]["mapped_attribute"] == "remarks"
        assert result.mapped_columns[2]["mapped_attribute"] == "transaction_type"
        assert result.mapped_columns[3]["mapped_attribute"] == "transaction_amount"

        # Verify LLM service call
        mock_llm_instance.send_message_async.assert_called_once()
        call_args = mock_llm_instance.send_message_async.call_args[1]
        assert "messages" in call_args
        assert call_args["model"] == "claude-3-5-sonnet-20240620"


@pytest.fixture
def sample_island_df():
    return pd.DataFrame(
        {
            "Date": [
                "17/10/2024",
                "17/10/2024",
                "16/10/2024",
                "16/10/2024",
                "16/10/2024",
            ],
            "HijriDate": [
                "1446-04-14",
                "1446-04-14",
                "1446-04-13",
                "1446-04-13",
                "1446-04-13",
            ],
            "Time": ["09:54", "04:02", "10:23", "10:23", "09:39"],
            "Description": [
                "Serie Payment Order",
                "POS- Retailer Cr.",
                "POS- Retailer Cr.",
                "POS- Retailer Cr.",
                "Serie Payment Order",
            ],
            "Remarks": [
                "Name: TABBY FINCO LIMITED CO/Bank: SAUDI BRITISH BANK /ARB to FINCO",
                "P1 Term PG127000 10/15 00:20:30 - 10/16 00:20:30 - TABBY",
                "P1 Term ARBSB193232 10/15 00:20:30 - 10/16 00:20:30 - TABBY SAUDI FOR COMMS",
                "P1 Term ARBSB083232 10/15 00:20:30 - 10/16 00:20:30 - TABBY SAUDI FOR COMMS",
                "Name: TABBY FINCO LIMITED CO/Bank: SAUDI BRITISH BANK /ARB to FINCO",
            ],
            "Credit": ["", "224078.69", "10114.77", "7577.41", ""],
            "Debit": ["250000", "", "", "", "490000"],
            "Balance": ["1759.11", "251759.11", "27680.42", "17565.65", "9988.24"],
            "Channel Type": [
                "Al-Rajhi Business",
                "ATM",
                "ATM",
                "ATM",
                "Al-Rajhi Business",
            ],
        }
    )


@pytest.fixture
def sample_mapped_columns():
    return [
        {
            "name": "Date",
            "type": "date",
            "region": "A2:A62",
            "mapped_attribute": "initiated_date",
            "attribute_type": "date",
        },
        {
            "name": "Time",
            "type": "date",
            "region": "C2:C62",
            "mapped_attribute": "updated_date",
            "attribute_type": "date",
        },
        {
            "name": "Description",
            "type": "string",
            "region": "D2:D62",
            "mapped_attribute": "transaction_type",
            "attribute_type": "string",
        },
        {
            "name": "Remarks",
            "type": "string",
            "region": "E2:E62",
            "mapped_attribute": "remarks",
            "attribute_type": "string",
        },
        {
            "name": "Credit",
            "type": "number",
            "region": "F2:F62",
            "mapped_attribute": "credit",
            "attribute_type": "float",
        },
        {
            "name": "Debit",
            "type": "number",
            "region": "G2:G62",
            "mapped_attribute": "debit",
            "attribute_type": "float",
        },
        {
            "name": "Balance",
            "type": "number",
            "region": "H2:H62",
            "mapped_attribute": "balance",
            "attribute_type": "float",
        },
        {
            "name": "Channel Type",
            "type": "string",
            "region": "I2:I62",
            "mapped_attribute": "transaction_sub_type",
            "attribute_type": "string",
        },
    ]


def test_extract_from_region(sample_island_df, sample_mapped_columns):
    # Test for initiated_date
    initiated_date = extract_from_region(
        sample_island_df, sample_mapped_columns, "initiated_date"
    )
    assert initiated_date

    # Test for updated_date (Time column)
    updated_date = extract_from_region(
        sample_island_df, sample_mapped_columns, "updated_date"
    )
    assert not updated_date

    # Test for an unmapped attribute
    unmapped = extract_from_region(
        sample_island_df, sample_mapped_columns, "closing_balance_updated_date"
    )
    assert not unmapped


def test_date_attribute_handling(sample_island_df, sample_mapped_columns):
    # Test for initiated_date
    initiated_date = extract_from_region(
        sample_island_df, sample_mapped_columns, "initiated_date"
    )
    assert initiated_date

    # Test for updated_date
    updated_date = extract_from_region(
        sample_island_df, sample_mapped_columns, "updated_date"
    )
    assert not updated_date

    # Test for closing_balance_updated_date
    closing_balance_updated_date = extract_from_region(
        sample_island_df, sample_mapped_columns, "closing_balance_updated_date"
    )
    assert not closing_balance_updated_date


# pytest pantheon/ai_agents/agents/file_import_agent/activities/column_mapping/tests/test_cm.py --cov=pantheon.ai_agents.agents.file_import_agent.activities.column_mapping --cov-report=term-missing
