import pdfplumber
import io
from typing import List
import structlog

from pantheon_v2.tools.common.pdf_parser.config import PDFParserConfig
from pantheon_v2.tools.common.pdf_parser.models import (
    ParsePDFParams,
    ParsedPDF,
    PDFPage,
)
from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.common.pdf_parser.helper import (
    extract_tables,
    extract_formatted_text,
)

logger = structlog.get_logger(__name__)


class PDFParserTool(BaseTool):
    def __init__(self, config: PDFParserConfig):
        self.config = config

    async def initialize(self) -> None:
        """Initialize the PDF parser tool"""
        try:
            logger.info("PDF parser tool initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize PDF parser tool", error=str(e))
            raise

    async def parse_pdf(self, params: ParsePDFParams) -> ParsedPDF:
        """Parse PDF content and extract its contents"""
        try:
            if len(params.pdf_content) > self.config.max_size:
                raise ValueError(
                    f"PDF content exceeds maximum size of {self.config.max_size} bytes"
                )

            pdf_pages: List[PDFPage] = []

            # Open PDF with pdfplumber
            with pdfplumber.open(io.BytesIO(params.pdf_content)) as pdf:
                metadata = pdf.metadata

                # Process each page
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = []

                    # Extract tables if requested
                    if params.extract_tables:
                        tables = extract_tables(self.config, page)

                    # Extract text while preserving formatting
                    text = extract_formatted_text(page)

                    pdf_pages.append(
                        PDFPage(page_number=page_num, text=text, tables=tables)
                    )

                parsed_pdf = ParsedPDF(
                    total_pages=len(pdf.pages), pages=pdf_pages, metadata=metadata or {}
                )

                return parsed_pdf

        except Exception as e:
            logger.error("Failed to parse PDF", error=str(e))
            raise
