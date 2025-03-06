import pytest
from unittest.mock import patch, AsyncMock
from pantheon.ai_agents.agents.file_import_agent.activities.analyze_statement.ans import (
    analyze_statement_activity,
)
from pantheon.ai_agents.agents.file_import_agent.activities.analyze_statement.schema.as_schema import (
    AnalyzeStatementInput,
)


@pytest.mark.asyncio
async def test_analyze_statement_success():
    with patch(
        "pantheon.ai_agents.agents.file_import_agent.activities.analyze_statement.helpers.as_helper.LLMService.send_message_async",
        new_callable=AsyncMock,
    ) as mock_send_message_async:
        # Mocked LLM response
        mock_response_content = (
            "Based on the provided inputs, I'll analyze the data and determine the best approach for splitting transactions into credit and debit columns. Here's my reasoning:\n\n"
            '1. Column Mapping Analysis:\n   The column mapping shows four columns: Date, Transaction Details, Debit/Credit, and Amount (INR). The presence of a specific "Debit/Credit" column (C1:C7) is significant for determining transaction types.\n\n'
            '2. Sample Data Analysis:\n   The sample data confirms the structure outlined in the column mapping. The "Debit/Credit" column explicitly states whether each transaction is a debit or credit. The "Amount (INR)" column shows amounts with a currency symbol (₹) but doesn\'t indicate the transaction type through positive or negative values.\n\n'
            "...\n\n"
            "<output>\n"
            '{\n  "parameters": {\n    "value_region": "D1:D7",\n    "type_region": "C1:C7"\n  }\n}\n'
            "</output>\n"
        )
        mock_send_message_async.return_value.content = mock_response_content

        # Create dummy input
        input_data = AnalyzeStatementInput(
            column_mapping=[
                {
                    "name": "Date",
                    "type": "date",
                    "region": "A1:A7",
                    "mapped_attribute": "initiated_date",
                },
                {
                    "name": "Transaction Details",
                    "type": "string",
                    "region": "B1:B7",
                    "mapped_attribute": "transaction_details",
                },
                {
                    "name": "Debit/Credit",
                    "type": "string",
                    "region": "C1:C7",
                    "mapped_attribute": "transaction_type",
                },
                {
                    "name": "Amount (INR)",
                    "type": "string",
                    "region": "D1:D7",
                    "mapped_attribute": "transaction_amount",
                },
            ],
            sample_data_csv="Date,Transaction Details,Debit/Credit,Amount (INR)\n"
            "14 Nov '23,NEERU ENTERPRISES GURGAON IN,Debit,₹ 898.00\n"
            "14 Nov '23,PAYTM Noida IN,Credit,₹ 1020.00",
            amount_column_name="Amount (INR)",
            amount_column_region="D1:D7",
        )

        # Expected output
        expected_output = {
            "parameters": {"value_region": "D1:D7", "type_region": "C1:C7"}
        }

        # Call the function
        result = await analyze_statement_activity(input_data)

        # Assertions
        assert result is not None
        assert result == expected_output
        mock_send_message_async.assert_awaited_once()


@pytest.mark.asyncio
async def test_analyze_statement_no_output_tag():
    with patch(
        "pantheon.ai_agents.agents.file_import_agent.activities.analyze_statement.helpers.as_helper.LLMService.send_message_async",
        new_callable=AsyncMock,
    ) as mock_send_message_async:
        # Mocked LLM response without <output> tags
        mock_response_content = "Some reasoning without output tags."

        mock_send_message_async.return_value.content = mock_response_content

        # Create dummy input
        input_data = AnalyzeStatementInput(
            column_mapping=[],
            sample_data_csv="",
            amount_column_name="",
            amount_column_region="",
        )

        # Call the function
        result = await analyze_statement_activity(input_data)

        # Assertions
        assert result is None
        mock_send_message_async.assert_awaited_once()


@pytest.mark.asyncio
async def test_analyze_statement_invalid_json():
    with patch(
        "pantheon.ai_agents.agents.file_import_agent.activities.analyze_statement.helpers.as_helper.LLMService.send_message_async",
        new_callable=AsyncMock,
    ) as mock_send_message_async:
        # Mocked LLM response with invalid JSON
        mock_response_content = "<output>Invalid JSON</output>"

        mock_send_message_async.return_value.content = mock_response_content

        # Create dummy input
        input_data = AnalyzeStatementInput(
            column_mapping=[],
            sample_data_csv="",
            amount_column_name="",
            amount_column_region="",
        )

        # Call the function
        result = await analyze_statement_activity(input_data)

        # Assertions
        assert result is None
        mock_send_message_async.assert_awaited_once()


# pytest pantheon/ai_agents/agents/file_import_agent/activities/analyze_statement/tests/test_as.py -v --cov=pantheon.ai_agents.agents.file_import_agent.activities.analyze_statement --cov-report=term-missing --cov-report=html
