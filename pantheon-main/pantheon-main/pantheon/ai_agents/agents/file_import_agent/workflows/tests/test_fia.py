import pytest
from pantheon.ai_agents.agents.file_import_agent.workflows.helpers.llm_cache import (
    extract_config,
    destruct,
    combine_column_info_and_mappings,
    split_excel_ref,
    update_region,
)
from pantheon.ai_agents.agents.file_import_agent.workflows.schema.fia_schema import (
    Action,
    AddCreditDebitConfig,
    ColumnInfo,
    ColumnMapping,
)

# Example config for testing
example_config = {
    "transformation_config": {
        "actions": [
            {
                "type": "add_credit_debit",
                "config": {
                    "config": {
                        "amount_column_region": "B1:B19",
                        "type_region": None,
                        "regex_credit": r"(?i)^\s*\+?\d+(\.\d+)?\s*$",
                        "regex_debit": r"(?i)^\s*-\d+(\.\d+)?\s*$",
                    }
                },
            },
            {
                "type": "extract_columns",
                "config": {
                    "column_mappings": [
                        {
                            "name": "Account Number",
                            "type": "number",
                            "region": "A1:A19",
                            "mapped_attribute": "account_number",
                            "attribute_type": "string",
                        },
                        {
                            "name": "Amount",
                            "type": "number",
                            "region": "B1:B19",
                            "mapped_attribute": "transaction_amount",
                            "attribute_type": "float",
                        },
                    ]
                },
            },
        ]
    },
    "unmapped_columns": ["tag", "status", "transaction_sub_type", "transaction_type"],
    "errors": [
        "The Amount column is mapped to transaction_amount as it's not clear if it represents credit or debit. Further investigation may be needed.",
        "Date columns (Booked Date, Value Date, Closing Balance Updated At) are stored as numbers, likely timestamps. Conversion to proper date format may be required.",
    ],
    "opening_balance": {"opening_balance": None},
}


def test_extract_config():
    actions = [
        Action(
            type="add_credit_debit",
            config={"config": {"amount_column_region": "B1:B19"}},
        ),
        Action(
            type="extract_columns",
            config={"column_mappings": [{"name": "Account Number"}]},
        ),
    ]

    assert extract_config(actions, "add_credit_debit") == {
        "amount_column_region": "B1:B19"
    }
    assert extract_config(actions, "extract_columns") == {
        "column_mappings": [{"name": "Account Number"}]
    }
    assert extract_config(actions, "non_existent_type") is None


def test_destruct():
    add_credit_debit_config, extract_columns_config, unmapped_columns, errors = (
        destruct(example_config)
    )

    assert isinstance(add_credit_debit_config, AddCreditDebitConfig)
    assert add_credit_debit_config.amount_column_region == "B1:B19"
    assert isinstance(extract_columns_config, list)
    assert len(extract_columns_config) == 2
    assert unmapped_columns == [
        "tag",
        "status",
        "transaction_sub_type",
        "transaction_type",
    ]
    assert len(errors) == 2


def test_destruct_with_invalid_config():
    invalid_config = {
        "transformation_config": {"actions": [{"type": "invalid_type", "config": {}}]}
    }
    result = destruct(invalid_config)
    assert result == (None, None, None, None)


def test_combine_column_info_and_mappings():
    column_info = [
        ColumnInfo(name="Account Number", type="number", region="A1:A10"),
        ColumnInfo(name="Amount", type="number", region="B1:B10"),
    ]
    column_mappings_template = [
        ColumnMapping(
            name="Account Number",
            mapped_attribute="account_number",
            attribute_type="string",
        ),
        ColumnMapping(
            name="Amount", mapped_attribute="transaction_amount", attribute_type="float"
        ),
    ]

    result = combine_column_info_and_mappings(column_info, column_mappings_template)

    assert len(result) == 2
    assert result[0]["name"] == "Account Number"
    assert result[0]["type"] == "number"
    assert result[0]["region"] == "A1:A10"
    assert result[0]["mapped_attribute"] == "account_number"
    assert result[0]["attribute_type"] == "string"


def test_combine_column_info_and_mappings_with_error():
    column_info = [
        ColumnInfo(name="Account Number", type="number", region="A1:A10"),
    ]
    column_mappings_template = [
        ColumnMapping(
            name="Invalid Name",
            mapped_attribute="account_number",
            attribute_type="string",
        ),
    ]

    result = combine_column_info_and_mappings(column_info, column_mappings_template)
    assert len(result) == 1
    assert result[0]["name"] == "Invalid Name"
    assert result[0]["mapped_attribute"] == "account_number"
    assert result[0]["attribute_type"] == "string"

    result = combine_column_info_and_mappings(123, column_mappings_template)
    assert result == []


def test_combine_column_info_and_mappings_with_exception():
    column_info = [
        ColumnInfo(name="Account Number", type="number", region="A1:A10"),
    ]
    column_mappings_template = [
        {"name": "Invalid Mapping"},  # This will cause an AttributeError
    ]

    result = combine_column_info_and_mappings(column_info, column_mappings_template)
    assert result == []


def test_split_excel_ref():
    assert split_excel_ref("A1") == ("A", "1")
    assert split_excel_ref("AB123") == ("AB", "123")
    assert split_excel_ref("1A") == ("A", "1")


def test_update_region():
    assert update_region("A1:A10", 2, 15) == "A2:A15"
    assert update_region("B5:B20", 1, 30) == "B1:B30"


def test_destruct_with_exception():
    invalid_config = {
        "transformation_config": {
            "actions": [
                {
                    "type": "add_credit_debit",
                    "config": {
                        "config": "invalid"  # This should be a dict, not a string
                    },
                }
            ]
        }
    }
    result = destruct(invalid_config)
    assert result == (None, None, None, None)


def test_extract_config_with_exception():
    actions = [
        Action(
            type="add_credit_debit", config={"config": {"invalid_key": "invalid_value"}}
        ),
    ]

    result = extract_config(actions, "add_credit_debit")
    assert result == {"invalid_key": "invalid_value"}

    # Test with a non-existent action type
    result = extract_config(actions, "non_existent_type")
    assert result is None

    # Test with an empty list of actions
    result = extract_config([], "add_credit_debit")
    assert result is None

    # Test to throw error
    result = extract_config(123, "add_credit_debit")
    assert result is None


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__])
