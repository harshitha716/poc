from typing import List
import structlog

from pantheon_v2.tools.common.pdf_parser.config import PDFParserConfig

logger = structlog.get_logger(__name__)


def extract_tables(config: PDFParserConfig, page) -> List[List[List[str]]]:
    """Extract tables from a page with custom settings"""
    try:
        tables = page.extract_tables(config.table_settings)
        # Clean up None values and convert to strings
        return [
            [
                [str(cell).strip() if cell is not None else "" for cell in row]
                for row in table
            ]
            for table in tables
        ]
    except Exception as e:
        logger.error("Failed to extract tables", error=str(e))
        return []


def extract_formatted_text(page) -> str:
    """Extract text while preserving formatting and document structure"""
    try:
        # Extract all elements with their positions and types
        elements = []

        # Extract words with position data
        words = page.extract_words(
            keep_blank_chars=True,
            x_tolerance=1.5,
            y_tolerance=1.5,
            extra_attrs=["size", "fontname"],
        )

        for word in words:
            elements.append(
                {
                    "type": "text",
                    "content": word["text"],
                    "top": word["top"],
                    "bottom": word["bottom"],
                    "x0": word["x0"],
                    "x1": word["x1"],
                    "size": word.get("size", 0),
                    "font": word.get("fontname", ""),
                }
            )

        # Sort elements by position (top to bottom, left to right)
        elements.sort(key=lambda e: (e["top"], e["x0"]))

        # Group elements into lines based on vertical position
        lines = []
        current_line = []
        current_top = None

        for element in elements:
            if current_top is None:
                current_top = element["top"]

            # Start new line if significant vertical difference or font/size change
            if abs(element["top"] - current_top) > 2 or (
                current_line
                and (
                    abs(current_line[-1]["size"] - element["size"]) > 1
                    or current_line[-1]["font"] != element["font"]
                )
            ):
                if current_line:
                    lines.append(current_line)
                    current_line = []
                current_top = element["top"]

            current_line.append(element)

        # Add last line
        if current_line:
            lines.append(current_line)

        # Build formatted text with appropriate spacing and line breaks
        formatted_lines = []
        for line in lines:
            # Calculate relative indentation
            indent = int((line[0]["x0"] / 10))  # Normalize indentation

            # Determine if line is likely a header based on font size
            is_header = any(e["size"] > 12 for e in line)

            # Build line text with preserved spacing
            line_text = " ".join(e["content"] for e in line)

            # Add appropriate formatting
            if is_header:
                line_text = "\n" + line_text + "\n"

            formatted_lines.append(" " * indent + line_text)

        return "\n".join(formatted_lines)

    except Exception as e:
        logger.error(
            "Failed to extract formatted text",
            error=str(e),
            error_type=type(e).__name__,
        )
        # Fallback to basic text extraction
        return page.extract_text() or ""
