from pantheon_v2.tools.common.ocr.tool import OCRTool
from pantheon_v2.tools.common.ocr.models import (
    OCRExtractInput,
    OCRExtractOutput,
)

from pantheon_v2.tools.core.activity_registry import ActivityRegistry


@ActivityRegistry.register_activity("Extract structured data from documents using OCR")
async def extract_ocr_data(params: OCRExtractInput) -> OCRExtractOutput:
    tool = OCRTool()
    await tool.initialize()
    return await tool.extract_data(params)
