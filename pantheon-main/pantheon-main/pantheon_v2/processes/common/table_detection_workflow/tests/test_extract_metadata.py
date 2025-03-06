import pytest
from unittest.mock import AsyncMock, patch
import pandas as pd

from pantheon_v2.processes.common.table_detection_workflow.business_logic.extract_metadata import (
    extract_metadata,
)
from pantheon_v2.processes.common.table_detection_workflow.business_logic.models import (
    LLMCallInput,
    LLMCallOutput,
)
from pantheon_v2.processes.common.table_detection_workflow.business_logic.constants import (
    MetadataMode,
)
from pantheon_v2.core.modelrouter.models.models import (
    GenerationRequest,
    ModelResponse,
)
from pantheon_v2.core.modelrouter.constants.constants import (
    SupportedLLMModels,
    RouterProvider,
)


@pytest.fixture
def sample_metadata_df():
    df = pd.DataFrame(
        {
            "Key": ["Invoice Number", "Date", "Total Amount"],
            "Value": ["INV-001", "2024-02-24", "$1000.00"],
        }
    )
    return df.to_json(orient="split")


@pytest.fixture
def mock_model_router():
    router = AsyncMock()
    response = ModelResponse(
        content='{"data": {"invoice_number": "INV-001", "date": "2024-02-24", "total_amount": 1000.00}}',
        parsed_response={
            "data": {
                "invoice_number": "INV-001",
                "date": "2024-02-24",
                "total_amount": 1000.00,
            }
        },
        raw_response="test response",
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        model="claude-3-sonnet-20240229",
    )
    router.generate = AsyncMock(return_value=response)
    return router


@pytest.mark.asyncio
async def test_extract_metadata_all_mode(sample_metadata_df, mock_model_router):
    """Test metadata extraction in ALL mode"""
    with patch(
        "pantheon_v2.processes.common.table_detection_workflow.business_logic.extract_metadata.ModelRouterFactory"
    ) as mock_factory:
        mock_factory.get_router.return_value = mock_model_router

        input_data = LLMCallInput(metadata_df=sample_metadata_df, mode=MetadataMode.ALL)

        result = await extract_metadata(input_data)

        assert isinstance(result, LLMCallOutput)
        assert result.extracted_data.data["invoice_number"] == "INV-001"

        # Verify correct template was used
        mock_factory.get_router.assert_called_once_with(RouterProvider.LITELLM)
        generate_call_args = mock_model_router.generate.call_args[0][0]
        assert isinstance(generate_call_args, GenerationRequest)
        assert generate_call_args.model_name == SupportedLLMModels.CLAUDE_3_7
        assert generate_call_args.temperature == 0.1


@pytest.mark.asyncio
async def test_extract_metadata_targeted_mode(sample_metadata_df, mock_model_router):
    """Test metadata extraction in TARGETED mode"""
    with patch(
        "pantheon_v2.processes.common.table_detection_workflow.business_logic.extract_metadata.ModelRouterFactory"
    ) as mock_factory:
        mock_factory.get_router.return_value = mock_model_router

        input_data = LLMCallInput(
            metadata_df=sample_metadata_df,
            mode=MetadataMode.TARGETED,
            target_attributes=["invoice_number", "date"],
        )

        result = await extract_metadata(input_data)

        assert isinstance(result, LLMCallOutput)
        assert result.extracted_data.data["invoice_number"] == "INV-001"
        assert result.extracted_data.data["date"] == "2024-02-24"


@pytest.mark.asyncio
async def test_extract_metadata_with_dict_input(sample_metadata_df, mock_model_router):
    """Test metadata extraction with dictionary input instead of LLMCallInput"""
    with patch(
        "pantheon_v2.processes.common.table_detection_workflow.business_logic.extract_metadata.ModelRouterFactory"
    ) as mock_factory:
        mock_factory.get_router.return_value = mock_model_router

        input_data = {"metadata_df": sample_metadata_df, "mode": MetadataMode.ALL}

        result = await extract_metadata(input_data)

        assert isinstance(result, LLMCallOutput)
        assert result.extracted_data is not None


@pytest.mark.asyncio
async def test_extract_metadata_error_handling():
    """Test error handling in metadata extraction"""
    with patch(
        "pantheon_v2.processes.common.table_detection_workflow.business_logic.extract_metadata.ModelRouterFactory"
    ) as mock_factory:
        mock_router = AsyncMock()
        mock_router.generate = AsyncMock(side_effect=Exception("Test error"))
        mock_factory.get_router.return_value = mock_router

        input_data = LLMCallInput(metadata_df="invalid_data", mode=MetadataMode.ALL)

        with pytest.raises(Exception) as exc_info:
            await extract_metadata(input_data)

        assert str(exc_info.value) == "Test error"
