import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import base64
from io import BytesIO
from pydantic import BaseModel
from PyPDF2 import PdfReader, PdfWriter

from pantheon_v2.tools.common.ocr.tool import OCRTool
from pantheon_v2.tools.common.ocr.models import (
    OCRExtractInput,
    OCRExtractOutput,
    ExtractionType,
)
from pantheon_v2.core.modelrouter.models.models import GenerationRequest
from pantheon_v2.core.modelrouter.constants.constants import SupportedLLMModels
from pantheon_v2.core.modelrouter.factory import ModelRouterFactory


# Test schema models
class MockInvoiceData(BaseModel):
    title: str
    amount: float
    invoice_number: str
    date: str


# Mock response data
MOCK_INVOICE_DATA = MockInvoiceData(
    title="Test Invoice", amount=1000.0, invoice_number="INV-001", date="2024-03-20"
)


# Create a proper base64 encoded PDF content for testing
def create_test_pdf_content() -> str:
    pdf_writer = PdfWriter()
    pdf_writer.add_blank_page(width=72, height=72)
    output_pdf = BytesIO()
    pdf_writer.write(output_pdf)
    pdf_bytes = output_pdf.getvalue()
    return base64.b64encode(pdf_bytes).decode("utf-8")


# Use PDF content instead of text content for testing
VALID_BASE64_CONTENT = create_test_pdf_content()


@pytest.fixture
def mock_router():
    mock = MagicMock()
    mock.generate = AsyncMock()
    return mock


@pytest.fixture
def tool(mock_router):
    with patch.object(ModelRouterFactory, "get_router", return_value=mock_router):
        tool = OCRTool()
        return tool


class TestOCRTool:
    @pytest.mark.asyncio
    async def test_extract_data_success(self, tool):
        # Mock response
        mock_completion = MagicMock()
        mock_completion.parsed_response = MOCK_INVOICE_DATA
        mock_completion.raw_response = "Extracted invoice data"
        mock_completion.finish_reason = "stop"
        tool.model_router.generate.return_value = mock_completion

        # Test input
        input_params = OCRExtractInput(
            file_content=[VALID_BASE64_CONTENT],
            extract_dto=MockInvoiceData,
            extraction_type=ExtractionType.INVOICE,
        )

        # Execute
        result = await tool.extract_data(input_params)

        # Assertions
        assert isinstance(result, OCRExtractOutput)
        assert result.extracted_data == MOCK_INVOICE_DATA
        assert result.extracted_data.title == "Test Invoice"
        assert result.extracted_data.amount == 1000.0

        # Verify model router call
        assert tool.model_router.generate.call_count == 1
        call_args = tool.model_router.generate.call_args
        assert isinstance(call_args.kwargs["request"], GenerationRequest)
        assert call_args.kwargs["request"].model_name == SupportedLLMModels.CLAUDE_3_5

    @pytest.mark.asyncio
    async def test_extract_data_empty_file_content(self, tool):
        with pytest.raises(ValueError, match="No file content provided"):
            await tool.extract_data(
                OCRExtractInput(
                    file_content=[],
                    extract_dto=MockInvoiceData,
                    extraction_type=ExtractionType.INVOICE,
                )
            )


class TestPDFHelper:
    def create_test_pdf(self, num_pages: int) -> str:
        """Helper function to create a test PDF with specified number of pages"""
        pdf_writer = PdfWriter()
        for _ in range(num_pages):
            pdf_writer.add_blank_page(width=72, height=72)
        output_pdf = BytesIO()
        pdf_writer.write(output_pdf)
        pdf_bytes = output_pdf.getvalue()
        return base64.b64encode(pdf_bytes).decode("utf-8")

    def count_pdf_pages(self, base64_content: str) -> int:
        """Helper function to count pages in a base64 encoded PDF"""
        pdf_bytes = base64.b64decode(base64_content)
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        return len(pdf_reader.pages)


class TestOCRConstants:
    def test_invoice_extract_prompt_path(self):
        # Test that the invoice extraction prompt path exists and points to the correct file
        from pantheon_v2.tools.common.ocr.constants import INVOICE_EXTRACT_PROMPT_PATH

        # Check that the path exists
        assert (
            INVOICE_EXTRACT_PROMPT_PATH.exists()
        ), f"Path {INVOICE_EXTRACT_PROMPT_PATH} does not exist"

        # Check that it's a file
        assert (
            INVOICE_EXTRACT_PROMPT_PATH.is_file()
        ), f"{INVOICE_EXTRACT_PROMPT_PATH} is not a file"

        # Check expected path components
        assert (
            "ocr_prompt_registry" in INVOICE_EXTRACT_PROMPT_PATH.parts
        ), "Missing 'ocr_prompt_registry' in path"
        assert (
            "invoice_extraction" in INVOICE_EXTRACT_PROMPT_PATH.parts
        ), "Missing 'invoice_extraction' in path"
        assert (
            "prompts" in INVOICE_EXTRACT_PROMPT_PATH.parts
        ), "Missing 'prompts' in path"
        assert (
            INVOICE_EXTRACT_PROMPT_PATH.name == "invoice_extraction_prompt.txt"
        ), f"Incorrect filename: {INVOICE_EXTRACT_PROMPT_PATH.name}"


# pytest --cov=pantheon_v2/tools/ocr --cov-report=term-missing pantheon_v2/tools/ocr/tests/ -v
