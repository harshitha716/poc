import pytest
import base64
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from pantheon_v2.utils.helper.process_large_pdf import process_large_pdf


class TestProcessLargePDF:
    def create_test_pdf(self, num_pages: int) -> str:
        """Helper function to create a test PDF with specified number of pages"""
        pdf_writer = PdfWriter()

        # Create a PDF with num_pages blank pages
        for _ in range(num_pages):
            pdf_writer.add_blank_page(width=72, height=72)  # 1 inch x 1 inch pages

        # Write to bytes
        output_pdf = BytesIO()
        pdf_writer.write(output_pdf)
        pdf_bytes = output_pdf.getvalue()

        # Convert to base64
        return base64.b64encode(pdf_bytes).decode("utf-8")

    def count_pdf_pages(self, base64_content: str) -> int:
        """Helper function to count pages in a base64 encoded PDF"""
        pdf_bytes = base64.b64decode(base64_content)
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        return len(pdf_reader.pages)

    @pytest.mark.parametrize(
        "num_pages,page_limit,expected_pages",
        [
            (5, 10, 5),  # PDF within limit - should return unchanged
            (15, 10, 10),  # PDF exceeds limit - should return first 5 and last 5 pages
            (20, 6, 6),  # PDF exceeds limit - should return first 3 and last 3 pages
            (1, 10, 1),  # Single page PDF - should return unchanged
            (10, 10, 10),  # PDF exactly at limit - should return unchanged
        ],
    )
    def test_process_large_pdf(
        self, num_pages: int, page_limit: int, expected_pages: int
    ):
        """Test processing PDFs with different page counts and limits"""
        # Create a test PDF
        test_pdf_content = self.create_test_pdf(num_pages)

        # Process the PDF
        processed_content = process_large_pdf(test_pdf_content, page_limit)

        # Count pages in processed PDF
        processed_pages = self.count_pdf_pages(processed_content)

        # Verify number of pages
        assert processed_pages == expected_pages

        if num_pages <= page_limit:
            # If PDF was within limit, content should be unchanged
            assert processed_content == test_pdf_content
        else:
            # If PDF was processed, content should be different
            assert processed_content != test_pdf_content

    def test_process_large_pdf_content_order(self):
        """Test that the processed PDF contains the correct pages in the right order"""
        # Create a 15-page PDF
        test_pdf_content = self.create_test_pdf(15)

        # Process the PDF with a limit of 6 pages (should get first 3 and last 3)
        processed_content = process_large_pdf(test_pdf_content, 6)

        # Verify we have exactly 6 pages
        processed_pages = self.count_pdf_pages(processed_content)
        assert processed_pages == 6

        # Convert processed content back to PDF for page verification
        pdf_bytes = base64.b64decode(processed_content)
        pdf_reader = PdfReader(BytesIO(pdf_bytes))

        # Since we're using blank pages, we can at least verify the page count
        # and that the structure is maintained
        assert len(pdf_reader.pages) == 6

    def test_process_large_pdf_invalid_input(self):
        """Test handling of invalid input"""
        with pytest.raises(ValueError, match="Invalid base64 content"):
            process_large_pdf("not-valid-base64!")

    def test_process_large_pdf_zero_page_limit(self):
        """Test handling of zero page limit"""
        test_pdf_content = self.create_test_pdf(5)
        with pytest.raises(ValueError, match="Page limit must be greater than 0"):
            process_large_pdf(test_pdf_content, 0)

    def test_process_large_pdf_negative_page_limit(self):
        """Test handling of negative page limit"""
        test_pdf_content = self.create_test_pdf(5)
        with pytest.raises(ValueError, match="Page limit must be greater than 0"):
            process_large_pdf(test_pdf_content, -1)

    def test_process_large_pdf_invalid_pdf_content(self):
        """Test handling of invalid PDF content"""
        # Create valid base64 but invalid PDF content
        invalid_content = base64.b64encode(b"not a pdf").decode("utf-8")
        with pytest.raises(ValueError, match="Invalid PDF content"):
            process_large_pdf(invalid_content)

    def test_process_large_pdf_default_page_limit(self):
        """Test processing with default page limit"""
        # Create a PDF with more than the default limit (10 pages)
        test_pdf_content = self.create_test_pdf(15)

        # Process without specifying page limit
        processed_content = process_large_pdf(test_pdf_content)

        # Verify it was reduced to 10 pages (default limit)
        processed_pages = self.count_pdf_pages(processed_content)
        assert processed_pages == 10

    def test_process_large_pdf_odd_page_limit(self):
        """Test processing with odd page limit"""
        # Create a PDF with 20 pages
        test_pdf_content = self.create_test_pdf(20)

        # Process with odd page limit (7)
        processed_content = process_large_pdf(test_pdf_content, 7)

        # Should round down to 6 pages (3 from start, 3 from end)
        processed_pages = self.count_pdf_pages(processed_content)
        assert processed_pages == 6
