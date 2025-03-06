import pytest
import io
from unittest.mock import Mock, patch
from reportlab.pdfgen import canvas
from pantheon_v2.tools.common.pdf_parser.tool import PDFParserTool, PDFParserConfig
from pantheon_v2.tools.common.pdf_parser.helper import (
    extract_formatted_text,
    extract_tables,
)
from pantheon_v2.tools.common.pdf_parser.models import ParsePDFParams, ParsedPDF


@pytest.fixture
def pdf_parser_config():
    config = {
        "max_size": 10_000_000,  # 10MB
        "table_settings": {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
        },
    }

    return PDFParserConfig(**config)


@pytest.fixture
def pdf_parser(pdf_parser_config):
    return PDFParserTool(pdf_parser_config)


@pytest.fixture
def sample_pdf_content():
    # Create a sample PDF in memory
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)

    # Add some text
    c.setFont("Helvetica", 14)
    c.drawString(100, 800, "Sample Header")
    c.setFont("Helvetica", 12)
    c.drawString(100, 780, "Regular text content")

    # Add table-like content
    y_position = 750
    for row in range(3):
        x_position = 100
        for col in range(3):
            c.drawString(x_position, y_position, f"Cell {row},{col}")
            x_position += 100
        y_position -= 20

    c.save()
    return buffer.getvalue()


async def test_parse_pdf_basic(pdf_parser, sample_pdf_content):
    params = ParsePDFParams(pdf_content=sample_pdf_content, extract_tables=True)
    result = await pdf_parser.parse_pdf(params)

    assert isinstance(result, ParsedPDF)
    assert result.total_pages == 1
    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert "Sample Header" in result.pages[0].text
    assert "Regular text content" in result.pages[0].text


async def test_parse_pdf_size_limit(pdf_parser):
    # Test with PDF content exceeding max_size
    pdf_parser.config.max_size = 10  # Set very small max size
    large_content = b"x" * 100  # Content larger than max_size

    with pytest.raises(ValueError) as exc_info:
        await pdf_parser.parse_pdf(ParsePDFParams(pdf_content=large_content))
    assert "PDF content exceeds maximum size" in str(exc_info.value)


@patch("pdfplumber.open")
async def test_parse_pdf_with_tables(mock_pdf_open, pdf_parser):
    # Mock PDF with tables
    mock_page = Mock()
    mock_page.extract_tables.return_value = [
        [["Header 1", "Header 2"], ["Data 1", "Data 2"]]
    ]
    mock_page.extract_words.return_value = [
        {
            "text": "Sample",
            "top": 100,
            "bottom": 110,
            "x0": 10,
            "x1": 50,
            "size": 12,
            "fontname": "Arial",
        },
        {
            "text": "Text",
            "top": 100,
            "bottom": 110,
            "x0": 60,
            "x1": 90,
            "size": 12,
            "fontname": "Arial",
        },
    ]

    mock_pdf = Mock()
    mock_pdf.pages = [mock_page]
    mock_pdf.metadata = {"Title": "Test PDF"}
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf

    params = ParsePDFParams(pdf_content=b"dummy content", extract_tables=True)
    result = await pdf_parser.parse_pdf(params)

    assert result.total_pages == 1
    assert len(result.pages[0].tables) == 1
    assert result.pages[0].tables[0][0] == ["Header 1", "Header 2"]
    assert result.metadata == {"Title": "Test PDF"}


def test_extract_formatted_text(pdf_parser):
    # Mock page with formatted text
    mock_page = Mock()
    mock_page.extract_words.return_value = [
        {
            "text": "Header",
            "top": 100,
            "bottom": 110,
            "x0": 10,
            "x1": 50,
            "size": 14,
            "fontname": "Arial",
        },
        {
            "text": "Content",
            "top": 120,
            "bottom": 130,
            "x0": 20,
            "x1": 60,
            "size": 12,
            "fontname": "Arial",
        },
        {
            "text": "Indented",
            "top": 120,
            "bottom": 130,
            "x0": 40,
            "x1": 80,
            "size": 12,
            "fontname": "Arial",
        },
    ]

    formatted_text = extract_formatted_text(mock_page)
    assert "Header" in formatted_text
    assert "Content" in formatted_text
    assert "Indented" in formatted_text


def test_extract_tables_error_handling(pdf_parser_config):
    mock_page = Mock()
    mock_page.extract_tables.side_effect = Exception("Table extraction failed")

    tables = extract_tables(pdf_parser_config, mock_page)
    assert tables == []  # Should return empty list on error


@pytest.mark.asyncio
async def test_parse_pdf_error_handling(pdf_parser):
    with pytest.raises(Exception):
        await pdf_parser.parse_pdf(ParsePDFParams(pdf_content=b"invalid pdf content"))


if __name__ == "__main__":
    pytest.main()
