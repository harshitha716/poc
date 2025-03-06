from pantheon_v2.core.prompt.generic import GenericPrompt
from pantheon_v2.core.prompt.models import PromptConfig
from pantheon_v2.core.common.models import MessageRole
from pantheon_v2.core.prompt.chain import PromptChain, ChainConfig
from typing import Union
import pandas as pd
from pathlib import Path
from pantheon_v2.core.modelrouter.models.models import (
    GenerationRequest,
)
from pantheon_v2.core.modelrouter.factory import ModelRouterFactory
import structlog

from pantheon_v2.processes.common.table_detection_workflow.business_logic.models import (
    ColumnMappingOutput,
    ColumnMappingInput,
)
from pantheon_v2.processes.common.table_detection_workflow.business_logic.constants import (
    DEFAULT_MODEL,
    DEFAULT_ROUTER_PROVIDER,
    DEFAULT_TEMPERATURE,
)

logger = structlog.get_logger(__name__)


def prepare_table_context(df_json: str, sample_rows: int = 3) -> str:
    """
    Prepare table context by including headers and sample data in a transposed format.
    If headers are numeric (likely row numbers), use the next row as headers.
    """
    try:
        df = pd.read_json(df_json, orient="split")

        # Check if headers are numeric
        headers = list(df.columns)
        are_headers_numeric = all(
            isinstance(h, (int, float)) or (isinstance(h, str) and h.isdigit())
            for h in headers
        )

        if are_headers_numeric:
            # Use first row as headers and rest as data
            new_headers = df.iloc[0].tolist()
            df.columns = new_headers
            df = df.iloc[1:].reset_index(drop=True)
            logger.info("Detected numeric headers, using first row as headers instead")

        # Get headers and sample data
        headers = list(df.columns)
        sample_data = df.head(sample_rows).T.to_string()

        return f"Headers: {headers}\nSample Data (Transposed):\n{sample_data}"
    except Exception as e:
        logger.error("Error preparing table context", error=str(e))
        raise


async def get_column_mapping_from_llm(
    source_context: str,
    target_context: str,
) -> ColumnMappingOutput:
    """
    Get column mapping suggestions from LLM.

    Args:
        source_context: Prepared context string for source table
        target_context: Prepared context string for target table

    Returns:
        ColumnMappingOutput containing the suggested mappings
    """
    # Create prompt with configuration
    prompt_path = Path(__file__).parent.parent / "prompts" / "column_mapping.txt"
    user_prompt = GenericPrompt(
        config=PromptConfig(
            template=str(prompt_path),  # Convert Path to string
            variables={
                "SOURCE_TABLE": source_context,
                "TARGET_TABLE": target_context,
            },
            role=MessageRole.USER,
        )
    )

    # Create chain with single prompt
    chain = PromptChain(
        config=ChainConfig(response_model=ColumnMappingOutput)
    ).add_prompt(user_prompt)
    logger.info("Created prompt chain for column mapping")

    # Create generation request
    request = GenerationRequest(
        prompt_chain=chain,
        model_name=DEFAULT_MODEL,
        temperature=DEFAULT_TEMPERATURE,
    )

    # Generate response
    model_router = ModelRouterFactory.get_router(DEFAULT_ROUTER_PROVIDER)
    response = await model_router.generate(request)
    return response.parsed_response


def apply_column_mapping(
    source_df: pd.DataFrame,
    mapping_result: ColumnMappingOutput,
) -> ColumnMappingOutput:
    """
    Apply the LLM-suggested column mapping to the source DataFrame.

    Args:
        source_df: Source DataFrame to be transformed
        mapping_result: ColumnMappingOutput from LLM

    Returns:
        ColumnMappingOutput containing the mapping results
    """
    # Create column mapping dictionary
    column_mapping = {
        m.source_column: m.target_column for m in mapping_result.mapped_columns
    }

    # Get list of source columns that were mapped
    mapped_source_columns = set(column_mapping.keys())

    # Keep only mapped columns and rename them
    normalized_df = source_df[list(mapped_source_columns)].rename(
        columns=column_mapping
    )

    # Log unmapped target columns
    if mapping_result.missing_columns and mapping_result.missing_columns.target:
        logger.info(
            "Found unmapped target columns",
            unmapped_target_columns=mapping_result.missing_columns.target,
        )

    # Add the normalized DataFrame to the result
    mapping_result.normalized_df = normalized_df.to_json(orient="split")

    logger.info(
        "Successfully normalized source DataFrame with mapped columns",
        num_columns=len(normalized_df.columns),
    )

    # Return the ColumnMappingOutput directly
    return mapping_result


async def execute_column_mapping(
    input_data: Union[dict, ColumnMappingInput],
) -> ColumnMappingOutput:
    """
    Execute column mapping using LLM to map between source and target formats.

    Args:
        input_data: ColumnMappingInput containing source and target DataFrames

    Returns:
        ColumnMappingOutput containing the mapping results
    """
    try:
        # Convert dict to ColumnMappingInput if necessary
        if isinstance(input_data, dict):
            input_data = ColumnMappingInput(**input_data)

        # Load source DataFrame
        source_df = pd.read_json(input_data.source_df, orient="split")

        # Check and fix numeric headers in source DataFrame
        headers = list(source_df.columns)
        are_headers_numeric = all(
            isinstance(h, (int, float)) or (isinstance(h, str) and h.isdigit())
            for h in headers
        )
        if are_headers_numeric:
            new_headers = source_df.iloc[0].tolist()
            source_df.columns = new_headers
            source_df = source_df.iloc[1:].reset_index(drop=True)

        # Prepare context for both source and target tables
        source_context = prepare_table_context(
            input_data.source_df, input_data.sample_rows
        )
        target_context = prepare_table_context(
            input_data.target_df, input_data.sample_rows
        )

        # Get mapping suggestions from LLM
        mapping_result = await get_column_mapping_from_llm(
            source_context, target_context
        )

        logger.info(
            "Successfully generated column mappings",
            document_type=mapping_result.document_type,
            confidence=mapping_result.confidence,
            num_mapped_columns=len(mapping_result.mapped_columns)
            if mapping_result.mapped_columns
            else 0,
        )

        # Apply the mapping to the DataFrame and return the ColumnMappingOutput
        result = apply_column_mapping(source_df, mapping_result)
        return result

    except Exception as e:
        logger.error("Error executing column mapping", error=str(e))
        raise
