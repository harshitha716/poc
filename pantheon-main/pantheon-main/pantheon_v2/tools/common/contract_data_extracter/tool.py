from __future__ import annotations

from pathlib import Path
from typing import TypeVar

import structlog
from pydantic import BaseModel

from pantheon_v2.core.modelrouter.models.models import (
    GenerationRequest,
)
from pantheon_v2.core.common.models import MessageRole
from pantheon_v2.core.modelrouter.constants.constants import SupportedLLMModels
from pantheon_v2.core.modelrouter.factory import ModelRouterFactory

from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.common.contract_data_extracter.models import (
    ContractDataExtracterInput,
    ContractDataExtracterOutput,
)
from pantheon_v2.tools.core.tool_registry import ToolRegistry
from pantheon_v2.core.prompt.models import PromptConfig
from pantheon_v2.core.prompt.chain import PromptChain
from pantheon_v2.core.prompt.generic import GenericPrompt
from pantheon_v2.core.modelrouter.constants.constants import RouterProvider
from pantheon_v2.core.prompt.chain import ChainConfig

logger = structlog.get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


@ToolRegistry.register_tool("ContractDataExtracterTool")
class ContractDataExtracterTool(BaseTool):
    """Tool for extracting structured data from documents using LLM."""

    def __init__(self):
        self.module_path = Path(__file__).parent
        self.model_router = ModelRouterFactory.get_router(RouterProvider.LITELLM)

    async def initialize(self):
        pass

    @ToolRegistry.register_tool_action("Extract data from the contract")
    async def extract_data(
        self, params: ContractDataExtracterInput
    ) -> ContractDataExtracterOutput[T]:
        """
        Extract data from a document based on the provided schema model.
        """
        # Create prompt with configuration
        user_prompt = GenericPrompt(
            config=PromptConfig(
                template="pantheon_v2/tools/common/contract_data_extracter/prompts/document_data_extraction_prompt.txt",
                variables={
                    "ADDITIONAL_PROMPT": params.additional_prompt or "",
                },
                role=MessageRole.USER,
            )
        )

        # Add document content as text
        user_prompt.add_text(params.document_content)

        # Create chain with single prompt
        chain = PromptChain(
            config=ChainConfig(response_model=params.output_model)
        ).add_prompt(user_prompt)

        # Create generation request
        request = GenerationRequest(
            prompt_chain=chain,
            model_name=SupportedLLMModels.GPT_O1,
            temperature=0.1,
        )

        # Generate response
        response = await self.model_router.generate(request)
        extracted_data = response.parsed_response

        logger.info("Data extracted successfully", model=params.output_model.__name__)
        return ContractDataExtracterOutput[params.output_model](
            extracted_data=extracted_data
        )
