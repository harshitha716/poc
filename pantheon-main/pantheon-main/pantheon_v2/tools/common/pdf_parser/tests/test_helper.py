from unittest.mock import Mock
from pantheon_v2.tools.common.pdf_parser.helper import (
    extract_tables,
    extract_formatted_text,
)
from pantheon_v2.tools.common.pdf_parser.config import PDFParserConfig

import pytest


class TestPDFParserHelper:
    @pytest.mark.asyncio
    def test_extract_tables_success(self):
        config = PDFParserConfig(
            max_size=10_000_000,
            table_settings={
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
            },
        )
        mock_page = Mock()
        mock_page.extract_tables.return_value = [
            [["Header 1", "Header 2"], [None, "Data 1"], ["Row 2", "Data 2"]]
        ]

        tables = extract_tables(config, mock_page)
        assert len(tables) == 1
        assert tables[0] == [
            ["Header 1", "Header 2"],
            ["", "Data 1"],
            ["Row 2", "Data 2"],
        ]
        mock_page.extract_tables.assert_called_once_with(config.table_settings)

    @pytest.mark.asyncio
    def test_extract_tables_error(self):
        config = PDFParserConfig(
            max_size=10_000_000,
            table_settings={
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
            },
        )
        mock_page = Mock()
        mock_page.extract_tables.side_effect = Exception("Table extraction failed")

        tables = extract_tables(config, mock_page)
        assert tables == []

    @pytest.mark.asyncio
    def test_extract_formatted_text_success(self):
        mock_page = Mock()
        mock_page.extract_words.return_value = [
            {
                "text": "Title",
                "top": 0,
                "bottom": 10,
                "x0": 0,
                "x1": 50,
                "size": 14,
                "fontname": "Arial-Bold",
            },
            {
                "text": "Content",
                "top": 20,
                "bottom": 30,
                "x0": 10,
                "x1": 60,
                "size": 12,
                "fontname": "Arial",
            },
            {
                "text": "Line",
                "top": 20,
                "bottom": 30,
                "x0": 70,
                "x1": 100,
                "size": 12,
                "fontname": "Arial",
            },
        ]

        text = extract_formatted_text(mock_page)
        assert "Title" in text
        assert "Content Line" in text

    @pytest.mark.asyncio
    def test_extract_formatted_text_with_indentation(self):
        mock_page = Mock()
        mock_page.extract_words.return_value = [
            {"text": "Level1", "top": 0, "bottom": 10, "x0": 0, "x1": 50, "size": 12},
            {"text": "Level2", "top": 20, "bottom": 30, "x0": 20, "x1": 70, "size": 12},
            {"text": "Level3", "top": 40, "bottom": 50, "x0": 40, "x1": 90, "size": 12},
        ]

        text = extract_formatted_text(mock_page)
        lines = text.split("\n")
        assert len(lines) >= 3
        assert lines[0].startswith("Level1")
        assert lines[1].startswith(" " * 2 + "Level2")
        assert lines[2].startswith(" " * 4 + "Level3")

    @pytest.mark.asyncio
    def test_extract_formatted_text_with_headers(self):
        mock_page = Mock()
        mock_page.extract_words.return_value = [
            {"text": "Header", "top": 0, "bottom": 10, "x0": 0, "x1": 50, "size": 14},
            {"text": "Normal", "top": 20, "bottom": 30, "x0": 0, "x1": 50, "size": 12},
        ]

        text = extract_formatted_text(mock_page)
        assert "\nHeader\n" in text
        assert "Normal" in text

    @pytest.mark.asyncio
    def test_extract_formatted_text_error(self):
        mock_page = Mock()
        mock_page.extract_words.side_effect = Exception("Word extraction failed")
        mock_page.extract_text.return_value = "Fallback text"

        text = extract_formatted_text(mock_page)
        assert text == "Fallback text"

    @pytest.mark.asyncio
    def test_extract_formatted_text_error_with_fallback_error(self):
        mock_page = Mock()
        mock_page.extract_words.side_effect = Exception("Word extraction failed")
        mock_page.extract_text.return_value = None

        text = extract_formatted_text(mock_page)
        assert text == ""
