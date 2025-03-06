from pantheon_v2.core.prompt.generic import GenericPrompt
from pantheon_v2.core.prompt.models import PromptConfig
from pantheon_v2.core.common.models import MessageRole
from pantheon_v2.core.prompt.chain import PromptChain, ChainConfig
from typing import Union
from pathlib import Path
from pantheon_v2.core.modelrouter.models.models import (
    GenerationRequest,
)
from pantheon_v2.core.modelrouter.constants.constants import (
    RouterProvider,
)
from pantheon_v2.core.modelrouter.factory import ModelRouterFactory
import structlog
import json
from pantheon_v2.processes.common.table_detection_workflow.business_logic.models import (
    MetadataOutput,
    LLMCallInput,
    LLMCallOutput,
)
from pantheon_v2.processes.common.table_detection_workflow.business_logic.constants import (
    MetadataMode,
    METADATA_TEMPLATE_TARGETED,
    METADATA_TEMPLATE_ALL,
    DEFAULT_MODEL,
)

logger = structlog.get_logger(__name__)


async def extract_metadata(input_data: Union[dict, LLMCallInput]) -> LLMCallOutput:
    """
    Execute an LLM call with the given prompt and metadata.

    Args:
        input_data: LLMCallInput containing prompt and metadata, or a dict with the same fields

    Returns:
        LLMCallOutput containing the extracted data
    """
    try:
        # Convert dict to LLMCallInput if necessary
        if isinstance(input_data, dict):
            input_data = LLMCallInput(**input_data)

        # Select the appropriate prompt template based on mode
        template_name = (
            METADATA_TEMPLATE_TARGETED
            if input_data.mode == MetadataMode.TARGETED
            else METADATA_TEMPLATE_ALL
        )

        # Create prompt with configuration
        prompt_path = Path(__file__).parent.parent / "prompts" / template_name
        user_prompt = GenericPrompt(
            config=PromptConfig(
                template=str(prompt_path),  # Convert Path to string
                variables={
                    "METADATA_TABLE": input_data.metadata_df,
                    "TARGET_ATTRIBUTES": json.dumps(input_data.target_attributes)
                    if input_data.target_attributes
                    else "[]",
                },
                role=MessageRole.USER,
            )
        )

        # Create chain with single prompt
        chain = PromptChain(
            config=ChainConfig(response_model=MetadataOutput)
        ).add_prompt(user_prompt)

        logger.info("Created prompt chain", chain=chain, mode=input_data.mode)

        # Create generation request
        request = GenerationRequest(
            prompt_chain=chain,
            model_name=DEFAULT_MODEL,
            temperature=0.1,
        )

        # Generate response
        model_router = ModelRouterFactory.get_router(RouterProvider.LITELLM)
        response = await model_router.generate(request)
        extracted_data = response.parsed_response

        logger.info("Successfully extracted data from LLM", mode=input_data.mode)
        output = LLMCallOutput(extracted_data=extracted_data)
        return output  # Return the BaseModel directly

    except Exception as e:
        logger.error("Error executing LLM call", error=str(e))
        raise
