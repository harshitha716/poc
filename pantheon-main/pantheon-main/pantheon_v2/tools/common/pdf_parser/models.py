from pydantic import BaseModel, Field
from typing import List


class PDFPage(BaseModel):
    page_number: int = Field(..., description="Page number in the PDF")
    text: str = Field(..., description="Extracted text content from the page")
    tables: List[List[List[str]]] = Field(
        default_factory=list, description="Tables extracted from the page"
    )

    def to_text(self) -> str:
        """Convert a single page to formatted text including tables"""
        parts = []

        # Add page number header
        parts.append(f"\n{'='*80}\n")
        parts.append(f"Page {self.page_number}\n")
        parts.append(f"{'='*80}\n\n")

        # Add main text content
        if self.text:
            parts.append(self.text)
            parts.append("\n")

        # Add tables if present
        if self.tables:
            for table_idx, table in enumerate(self.tables, 1):
                parts.append(f"\nTable {table_idx}:\n")
                parts.append("-" * 80 + "\n")

                # Calculate column widths
                col_widths = []
                for col in range(len(table[0])):
                    width = max(len(str(row[col])) for row in table)
                    col_widths.append(min(width, 30))  # Cap width at 30 chars

                # Format each row
                for row in table:
                    formatted_row = []
                    for cell, width in zip(row, col_widths):
                        formatted_row.append(str(cell).ljust(width))
                    parts.append("| " + " | ".join(formatted_row) + " |\n")

                parts.append("-" * 80 + "\n")

        return "".join(parts)


class ParsedPDF(BaseModel):
    total_pages: int = Field(..., description="Total number of pages in the PDF")
    pages: List[PDFPage] = Field(..., description="List of parsed pages")
    metadata: dict = Field(default_factory=dict, description="PDF metadata")

    def to_text(self, include_metadata: bool = True) -> str:
        """
        Convert the entire PDF to a formatted text representation

        Args:
            include_metadata (bool): Whether to include PDF metadata in the output

        Returns:
            str: Formatted text representation of the PDF
        """
        parts = []

        # Add metadata section if requested
        if include_metadata and self.metadata:
            parts.append("METADATA:\n")
            parts.append("=" * 80 + "\n")
            for key, value in self.metadata.items():
                if value:  # Only include non-empty metadata
                    parts.append(f"{key}: {value}\n")
            parts.append("=" * 80 + "\n\n")

        # Add content from each page
        for page in self.pages:
            parts.append(page.to_text())

        return "".join(parts)


class ParsePDFParams(BaseModel):
    pdf_content: bytes = Field(..., description="Raw PDF content as bytes")
    extract_tables: bool = Field(
        default=True,
        description="Whether to extract tables from the PDF",
    )
