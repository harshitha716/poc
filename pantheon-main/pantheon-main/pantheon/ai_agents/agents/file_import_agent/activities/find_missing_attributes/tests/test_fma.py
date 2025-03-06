import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, AsyncMock
from pantheon.ai_agents.agents.file_import_agent.activities.find_missing_attributes.fma import (
    find_missing_attributes_activity,
)
from pantheon.ai_agents.agents.file_import_agent.activities.find_missing_attributes.schema.fma_schema import (
    FindMissingAttributesInput,
    FindMissingAttributesOutput,
)
from pantheon.ai_agents.agents.file_import_agent.activities.find_missing_attributes.helpers.fma_helper import (
    MissingAttributesAgent,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            0: ["", "", "", "", "", "Date", "2023-05-01", "2023-05-02", "2023-05-03"],
            1: ["", "account_number", "account_name", "", "", "Value", 100, 200, 300],
            2: ["", "12345", "Some account name", "", "", "Category", "A", "B", "C"],
        }
    )


@pytest.fixture
def mock_llm_response():
    return MagicMock(
        role="assistant",
        content='{\n    "account_number": {\n        "value": "12345",\n        "attribute_type": "string"\n    },\n    "account_name": {\n        "value": "Some account name",\n        "attribute_type": "string"\n    }\n}',
    )


@pytest.mark.asyncio
async def test_find_missing_attributes_activity(sample_df, mock_llm_response):
    with patch(
        "pantheon.ai_agents.agents.file_import_agent.activities.find_missing_attributes.helpers.fma_helper.LLMService"
    ) as MockLLMService:
        mock_llm_service = MockLLMService.return_value
        mock_llm_service.send_message_async = AsyncMock(return_value=mock_llm_response)

        input_data = FindMissingAttributesInput(
            original_df=sample_df,
            region="A5:C9",
            unmapped_attributes=[
                "account_number",
                "account_name",
                "currency",
                "iban",
                "bic_code",
            ],
        )

        result = await find_missing_attributes_activity(input_data)

        assert isinstance(result, FindMissingAttributesOutput)
        assert len(result.mapped_attributes) == 2
        assert result.mapped_attributes[0]["name"] == "account_number"
        assert result.mapped_attributes[0]["value"] == "12345"
        assert result.mapped_attributes[0]["attribute_type"] == "string"
        assert result.mapped_attributes[0]["region"] == "A5:C9"
        assert result.mapped_attributes[1]["name"] == "account_name"
        assert result.mapped_attributes[1]["value"] == "Some account name"
        assert result.mapped_attributes[1]["attribute_type"] == "string"
        assert result.mapped_attributes[1]["region"] == "A5:C9"
        assert result.search_still_unmapped == ["currency", "iban", "bic_code"]
        assert result.opening_balance == {"opening_balance": None}

        mock_llm_service.send_message_async.assert_called_once()


@pytest.mark.asyncio
async def test_find_missing_attributes_activity_invalid_region(sample_df):
    input_data = FindMissingAttributesInput(
        original_df=sample_df,
        region="invalid_region",
        unmapped_attributes=[
            "account_number",
            "account_name",
            "currency",
            "iban",
            "bic_code",
        ],
    )

    result = await find_missing_attributes_activity(input_data)

    assert isinstance(result, FindMissingAttributesOutput)
    assert len(result.mapped_attributes) == 0
    assert result.search_still_unmapped == [
        "account_number",
        "account_name",
        "currency",
        "iban",
        "bic_code",
    ]
    assert result.opening_balance == {"opening_balance": None}


@pytest.mark.asyncio
async def test_find_missing_attributes_activity_entire_dataframe(sample_df):
    input_data = FindMissingAttributesInput(
        original_df=sample_df,
        region="A1:C9",
        unmapped_attributes=[
            "account_number",
            "account_name",
            "currency",
            "iban",
            "bic_code",
        ],
    )

    result = await find_missing_attributes_activity(input_data)

    assert isinstance(result, FindMissingAttributesOutput)
    assert len(result.mapped_attributes) == 0
    assert result.search_still_unmapped == [
        "account_number",
        "account_name",
        "currency",
        "iban",
        "bic_code",
    ]
    assert result.opening_balance == {"opening_balance": None}


@pytest.mark.asyncio
async def test_find_missing_attributes_activity_exception(sample_df, mock_llm_response):
    with patch(
        "pantheon.ai_agents.agents.file_import_agent.activities.find_missing_attributes.helpers.fma_helper.LLMService"
    ) as MockLLMService:
        mock_llm_service = MockLLMService.return_value
        mock_llm_service.send_message_async.side_effect = Exception("LLM service error")

        input_data = FindMissingAttributesInput(
            original_df=sample_df,
            region="A5:C9",
            unmapped_attributes=[
                "account_number",
                "account_name",
                "currency",
                "iban",
                "bic_code",
            ],
        )

        result = await find_missing_attributes_activity(input_data)
        assert result.mapped_attributes == []
        assert result.search_still_unmapped == [
            "account_number",
            "account_name",
            "currency",
            "iban",
            "bic_code",
        ]
        assert result.opening_balance == {"opening_balance": None}

        result = await find_missing_attributes_activity("123")
        assert result is None


@pytest.mark.asyncio
async def test_missing_attributes_agent_format_prompt(sample_df):
    agent = MissingAttributesAgent()
    unmapped_attributes = ["account_number", "account_name"]
    cleaned_data_str = sample_df.to_string(index=False, header=False, na_rep="")

    formatted_prompt = agent._format_prompt(unmapped_attributes, cleaned_data_str)

    assert isinstance(formatted_prompt, str)
    assert "account_number" in formatted_prompt
    assert "account_name" in formatted_prompt
    assert cleaned_data_str in formatted_prompt


@pytest.mark.asyncio
async def test_missing_attributes_agent_validate_llm_response():
    response_json = {
        "account_number": {"value": "12345", "attribute_type": "string"},
        "account_name": {"value": "Some account name", "attribute_type": "string"},
        "opening_balance": {"value": "1000", "attribute_type": "number"},
    }
    region = "A5:C9"

    validated_response, opening_balance = MissingAttributesAgent._validate_llm_response(
        response_json, region
    )

    assert len(validated_response) == 2
    assert validated_response[0]["name"] == "account_number"
    assert validated_response[0]["value"] == "12345"
    assert validated_response[0]["attribute_type"] == "string"
    assert validated_response[0]["region"] == "A5:C9"
    assert validated_response[1]["name"] == "account_name"
    assert validated_response[1]["value"] == "Some account name"
    assert validated_response[1]["attribute_type"] == "string"
    assert validated_response[1]["region"] == "A5:C9"
    assert opening_balance == {"opening_balance": "1000"}


# Add more tests for fma_tools.py functions
@pytest.mark.parametrize(
    "region, expected",
    [
        ("A1:B2", ("A", 1, "B", 2)),
        ("C3:D4", ("C", 3, "D", 4)),
        ("invalid_region", None),
    ],
)
def test_parse_region(region, expected):
    from pantheon.ai_agents.agents.file_import_agent.activities.find_missing_attributes.helpers.fma_tools import (
        parse_region,
    )

    assert parse_region(region) == expected


def test_is_entire_dataframe():
    from pantheon.ai_agents.agents.file_import_agent.activities.find_missing_attributes.helpers.fma_tools import (
        is_entire_dataframe,
    )

    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    assert is_entire_dataframe(0, "A", 2, "B", df)
    assert not is_entire_dataframe(1, "A", 2, "B", df)


def test_column_to_index():
    from pantheon.ai_agents.agents.file_import_agent.activities.find_missing_attributes.helpers.fma_tools import (
        column_to_index,
    )

    assert column_to_index("A") == 0
    assert column_to_index("B") == 1
    assert column_to_index("Z") == 25
    assert column_to_index("AA") == 26


# pytest pantheon/ai_agents/agents/file_import_agent/activities/find_missing_attributes/tests/test_fma.py -v --cov=pantheon.ai_agents.agents.file_import_agent.activities.find_missing_attributes --cov-report=term-missing
