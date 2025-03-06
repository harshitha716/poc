from pantheon_v2.tools.common.pdf_parser.tool import PDFParserTool
from pantheon_v2.tools.common.pdf_parser.config import PDFParserConfig
from pantheon_v2.tools.common.pdf_parser.models import ParsePDFParams, ParsedPDF

from pantheon_v2.tools.core.activity_registry import ActivityRegistry


@ActivityRegistry.register_activity("Parse PDF content and extract its contents")
async def parse_pdf(config: PDFParserConfig, params: ParsePDFParams) -> ParsedPDF:
    """Parse PDF content and extract its contents"""
    tool = PDFParserTool(config)
    return await tool.parse_pdf(params)
