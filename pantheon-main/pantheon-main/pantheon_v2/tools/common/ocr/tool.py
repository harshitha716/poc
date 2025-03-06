import structlog

from pantheon_v2.core.modelrouter.constants.constants import SupportedLLMModels
from pantheon_v2.core.modelrouter.models.models import GenerationRequest
from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.core.tool_registry import ToolRegistry
from pantheon_v2.tools.common.ocr.models import (
    OCRExtractInput,
    OCRExtractOutput,
    ExtractionType,
    FileContent,
)
from pantheon_v2.utils.helper.process_large_pdf import process_large_pdf
from pantheon_v2.core.prompt.models import PromptConfig
from pantheon_v2.core.common.models import MessageRole
from pantheon_v2.core.prompt.generic import GenericPrompt
from pantheon_v2.core.prompt.chain import PromptChain, ChainConfig
from pantheon_v2.core.modelrouter.factory import ModelRouterFactory
from pantheon_v2.core.modelrouter.constants.constants import RouterProvider
from pantheon_v2.utils.file_utils import infer_file_type
from pantheon_v2.tools.common.ocr.constants import INVOICE_EXTRACT_PROMPT_PATH


logger = structlog.get_logger(__name__)


@ToolRegistry.register_tool(
    description="OCR tool for extracting structured JSON data from documents"
)
class OCRTool(BaseTool):
    def __init__(self):
        self.model_router = ModelRouterFactory.get_router(RouterProvider.LITELLM)

    async def initialize(self) -> None:
        """Initialize the OCR client asynchronously"""
        try:
            logger.info("OCR tool initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize OCR tool", error=str(e))
            raise

    def _process_file_content(
        self, file: str, file_type: str, page_limit: int
    ) -> FileContent:
        """Process file content and return FileContent DTO"""
        if file_type == "text":
            return FileContent(
                file_content=file,
                file_type=file_type,
                file_url=file,
                content_type="text",
            )

        if file_type == "application/pdf":
            file = process_large_pdf(file, page_limit)

        return FileContent(
            file_content=file,
            file_type=file_type,
            file_url=f"data:{file_type};base64,{file}",
            content_type="image_url",
        )

    def get_extraction_prompt_config(
        self, extraction_type: ExtractionType
    ) -> PromptConfig:
        """Get the appropriate extraction registry based on type"""
        match extraction_type:
            case ExtractionType.CONTRACT:
                raise ValueError("Contract extraction not supported yet")
            case ExtractionType.INVOICE | None:
                prompt_path = INVOICE_EXTRACT_PROMPT_PATH
                # Convert Path to string
                prompt_config = PromptConfig(
                    template=str(prompt_path),
                    role=MessageRole.USER,
                )
                return prompt_config
            case _:
                raise ValueError(f"Unsupported extraction type: {extraction_type}")

    @ToolRegistry.register_tool_action(
        description="Extract structured data from documents using OCR"
    )
    async def extract_data(self, params: OCRExtractInput) -> OCRExtractOutput:
        """Extract structured data from documents using OCR."""
        if not params.file_content:
            raise ValueError("No file content provided")

        # Check extraction configuration before Pydantic validation
        if not params.extraction_type and not params.extract_dto:
            raise ValueError("Either extraction_type or extract_dto must be provided")

        # Get extraction configuration
        output_dto = params.extract_dto
        if params.extraction_type:
            prompt_config = self.get_extraction_prompt_config(params.extraction_type)
            prompt = GenericPrompt(
                config=prompt_config,
            )

            # Process files
            page_limit = 100  # Default page limit
            for file in params.file_content:
                file_type = infer_file_type(file)
                file_content = self._process_file_content(file, file_type, page_limit)
                if file_content.content_type == "text":
                    prompt.add_text(file_content.file_content)
                else:
                    prompt.add_file(file_content.file_content)

            promptchain = PromptChain(
                config=ChainConfig(response_model=output_dto),
            ).add_prompt(prompt)

            response = await self.model_router.generate(
                request=GenerationRequest(
                    prompt_chain=promptchain,
                    model_name=SupportedLLMModels.CLAUDE_3_5,
                    temperature=0.1,
                )
            )

            return OCRExtractOutput[params.extract_dto](
                extracted_data=params.extract_dto.model_validate(
                    response.parsed_response
                )
            )
