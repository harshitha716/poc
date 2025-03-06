import pytest
from unittest.mock import AsyncMock, patch
import pandas as pd
import json
from pydantic import BaseModel
from typing import Dict, Any, List, Union

from pantheon_v2.processes.common.table_detection_workflow.business_logic.column_mapping_llm_call import (
    prepare_table_context,
    get_column_mapping_from_llm,
    apply_column_mapping,
    execute_column_mapping,
)
from pantheon_v2.processes.common.table_detection_workflow.business_logic.models import (
    ColumnMappingOutput,
    ColumnMappingInput,
    ColumnMapping,
    MissingColumns,
)
from pantheon_v2.core.modelrouter.models.models import (
    ModelResponse,
    GenerationRequest,
)
from pantheon_v2.core.modelrouter.constants.constants import (
    SupportedLLMModels,
    RouterProvider,
)


# Create a model to wrap dictionary results
class MappingResult(BaseModel):
    normalized_df: str
    mapped_columns: List[Union[Dict[str, Any], ColumnMapping]]

    class Config:
        arbitrary_types_allowed = True


@pytest.fixture
def sample_df():
    df = pd.DataFrame(
        {
            "Invoice_No": ["INV001", "INV002"],
            "Amount": [100.0, 200.0],
            "Date": ["2024-01-01", "2024-01-02"],
        }
    )
    return df.to_json(orient="split")


@pytest.fixture
def sample_df_numeric_headers():
    df = pd.DataFrame(
        {
            "1": ["Invoice Number", "INV001", "INV002"],
            "2": ["Amount", 100.0, 200.0],
            "3": ["Date", "2024-01-01", "2024-01-02"],
        }
    )
    return df.to_json(orient="split")


@pytest.fixture
def sample_mapping_output():
    return ColumnMappingOutput(
        mapped_columns=[
            ColumnMapping(
                source_column="Invoice_No",
                target_column="invoice_number",
                confidence=0.95,
                mapping_reason="Exact semantic match",
            ),
            ColumnMapping(
                source_column="Amount",
                target_column="total_amount",
                confidence=0.9,
                mapping_reason="Semantic similarity",
            ),
        ],
        missing_columns=MissingColumns(source=["Date"], target=["customer_id"]),
        document_type="Invoice",
        confidence=0.92,
    )


@pytest.fixture
def mock_model_router():
    router = AsyncMock()
    response = ModelResponse(
        content=json.dumps(
            {
                "mapped_columns": [
                    {
                        "source_column": "Invoice_No",
                        "target_column": "invoice_number",
                        "confidence": 0.95,
                        "mapping_reason": "Exact semantic match",
                    }
                ],
                "missing_columns": {"source": ["Date"], "target": ["customer_id"]},
                "document_type": "Invoice",
                "confidence": 0.92,
            }
        ),
        parsed_response=ColumnMappingOutput(
            mapped_columns=[
                ColumnMapping(
                    source_column="Invoice_No",
                    target_column="invoice_number",
                    confidence=0.95,
                    mapping_reason="Exact semantic match",
                )
            ],
            missing_columns=MissingColumns(source=["Date"], target=["customer_id"]),
            document_type="Invoice",
            confidence=0.92,
        ),
        raw_response="test response",
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        model="claude-3-sonnet-20240229",
    )
    router.generate = AsyncMock(return_value=response)
    return router


@pytest.fixture
def mock_model_router_numeric():
    router = AsyncMock()
    response = ModelResponse(
        content=json.dumps(
            {
                "mapped_columns": [
                    {
                        "source_column": "Invoice Number",
                        "target_column": "invoice_number",
                        "confidence": 0.95,
                        "mapping_reason": "Exact semantic match",
                    }
                ],
                "missing_columns": {"source": ["Date"], "target": ["customer_id"]},
                "document_type": "Invoice",
                "confidence": 0.92,
            }
        ),
        parsed_response=ColumnMappingOutput(
            mapped_columns=[
                ColumnMapping(
                    source_column="Invoice Number",
                    target_column="invoice_number",
                    confidence=0.95,
                    mapping_reason="Exact semantic match",
                )
            ],
            missing_columns=MissingColumns(source=["Date"], target=["customer_id"]),
            document_type="Invoice",
            confidence=0.92,
        ),
        raw_response="test response",
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        model="claude-3-sonnet-20240229",
    )
    router.generate = AsyncMock(return_value=response)
    return router


def test_prepare_table_context_normal(sample_df):
    """Test prepare_table_context with normal headers"""
    result = prepare_table_context(sample_df)
    assert "Headers: " in result
    assert "Invoice_No" in result
    assert "Amount" in result
    assert "Date" in result
    assert "Sample Data (Transposed)" in result


def test_prepare_table_context_numeric_headers(sample_df_numeric_headers):
    """Test prepare_table_context with numeric headers"""
    result = prepare_table_context(sample_df_numeric_headers)
    assert "Headers: " in result
    assert "Invoice Number" in result
    assert "Amount" in result
    assert "Date" in result


def test_prepare_table_context_invalid_json():
    """Test prepare_table_context with invalid JSON"""
    with pytest.raises(Exception):
        prepare_table_context("invalid json")


@pytest.mark.asyncio
async def test_get_column_mapping_from_llm(mock_model_router):
    """Test get_column_mapping_from_llm function"""
    with patch(
        "pantheon_v2.processes.common.table_detection_workflow.business_logic.column_mapping_llm_call.ModelRouterFactory"
    ) as mock_factory:
        mock_factory.get_router.return_value = mock_model_router

        result = await get_column_mapping_from_llm("source context", "target context")

        assert isinstance(result, ColumnMappingOutput)
        assert result.document_type == "Invoice"
        assert len(result.mapped_columns) == 1
        assert result.mapped_columns[0].source_column == "Invoice_No"

        # Verify correct router and model were used
        mock_factory.get_router.assert_called_once_with(RouterProvider.LITELLM)
        generate_call_args = mock_model_router.generate.call_args[0][0]
        assert isinstance(generate_call_args, GenerationRequest)
        assert generate_call_args.model_name == SupportedLLMModels.CLAUDE_3_7
        assert generate_call_args.temperature == 0.1


def test_apply_column_mapping(sample_df, sample_mapping_output):
    """Test apply_column_mapping function"""
    df = pd.read_json(sample_df, orient="split")
    result = apply_column_mapping(df, sample_mapping_output)

    # Convert ColumnMapping objects to dictionaries if needed
    mapped_columns = [
        mapping.model_dump() if isinstance(mapping, ColumnMapping) else mapping
        for mapping in result.mapped_columns
    ]

    # Wrap the result in our model
    result_model = MappingResult(
        normalized_df=result.normalized_df, mapped_columns=mapped_columns
    )

    assert isinstance(result_model, MappingResult)
    assert result_model.normalized_df is not None
    assert result_model.mapped_columns is not None

    # Load the normalized DataFrame
    normalized_df = pd.read_json(result_model.normalized_df, orient="split")
    assert "invoice_number" in normalized_df.columns
    assert "total_amount" in normalized_df.columns
    assert "Date" not in normalized_df.columns  # Unmapped column should be excluded


@pytest.mark.asyncio
async def test_execute_column_mapping_with_dict_input(sample_df, mock_model_router):
    """Test execute_column_mapping with dictionary input"""
    with patch(
        "pantheon_v2.processes.common.table_detection_workflow.business_logic.column_mapping_llm_call.ModelRouterFactory"
    ) as mock_factory:
        mock_factory.get_router.return_value = mock_model_router

        input_data = {
            "source_df": sample_df,
            "target_df": sample_df,  # Using same DF for simplicity
            "sample_rows": 2,
        }

        result = await execute_column_mapping(input_data)

        # Convert ColumnMapping objects to dictionaries if needed
        mapped_columns = [
            mapping.model_dump() if isinstance(mapping, ColumnMapping) else mapping
            for mapping in result.mapped_columns
        ]

        # Wrap the result in our model
        result_model = MappingResult(
            normalized_df=result.normalized_df, mapped_columns=mapped_columns
        )

        assert isinstance(result_model, MappingResult)
        assert result_model.normalized_df is not None
        assert result_model.mapped_columns is not None


@pytest.mark.asyncio
async def test_execute_column_mapping_with_model_input(sample_df, mock_model_router):
    """Test execute_column_mapping with ColumnMappingInput"""
    with patch(
        "pantheon_v2.processes.common.table_detection_workflow.business_logic.column_mapping_llm_call.ModelRouterFactory"
    ) as mock_factory:
        mock_factory.get_router.return_value = mock_model_router

        input_data = ColumnMappingInput(
            source_df=sample_df,
            target_df=sample_df,  # Using same DF for simplicity
            sample_rows=2,
        )

        result = await execute_column_mapping(input_data)

        # Convert ColumnMapping objects to dictionaries if needed
        mapped_columns = [
            mapping.model_dump() if isinstance(mapping, ColumnMapping) else mapping
            for mapping in result.mapped_columns
        ]

        # Wrap the result in our model
        result_model = MappingResult(
            normalized_df=result.normalized_df, mapped_columns=mapped_columns
        )

        assert isinstance(result_model, MappingResult)
        assert result_model.normalized_df is not None
        assert result_model.mapped_columns is not None


@pytest.mark.asyncio
async def test_execute_column_mapping_with_numeric_headers(
    sample_df_numeric_headers, mock_model_router_numeric
):
    """Test execute_column_mapping with numeric headers"""
    with patch(
        "pantheon_v2.processes.common.table_detection_workflow.business_logic.column_mapping_llm_call.ModelRouterFactory"
    ) as mock_factory:
        mock_factory.get_router.return_value = mock_model_router_numeric

        input_data = ColumnMappingInput(
            source_df=sample_df_numeric_headers,
            target_df=sample_df_numeric_headers,
            sample_rows=2,
        )

        result = await execute_column_mapping(input_data)

        # Convert ColumnMapping objects to dictionaries if needed
        mapped_columns = [
            mapping.model_dump() if isinstance(mapping, ColumnMapping) else mapping
            for mapping in result.mapped_columns
        ]

        # Wrap the result in our model
        result_model = MappingResult(
            normalized_df=result.normalized_df, mapped_columns=mapped_columns
        )

        assert isinstance(result_model, MappingResult)
        assert result_model.normalized_df is not None
        assert result_model.mapped_columns is not None

        # Load the normalized DataFrame to verify the mapping worked
        normalized_df = pd.read_json(result_model.normalized_df, orient="split")
        assert "invoice_number" in normalized_df.columns


@pytest.mark.asyncio
async def test_execute_column_mapping_error_handling():
    """Test execute_column_mapping error handling"""
    with pytest.raises(Exception):
        await execute_column_mapping(
            {"source_df": "invalid json", "target_df": "invalid json", "sample_rows": 2}
        )
