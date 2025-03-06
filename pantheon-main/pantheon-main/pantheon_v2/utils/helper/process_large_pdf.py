import io
import base64
from PyPDF2 import PdfReader, PdfWriter


def process_large_pdf(file_content: str, page_limit: int = 10) -> str:
    """
    Process PDF files that exceed the page limit by keeping only the first and last N/2 pages.

    Args:
        file_content (str): The original PDF file content as Base64 encoded string
        page_limit (int): Maximum number of pages before truncating (default: 10)

    Returns:
        str: Processed PDF content as Base64 encoded string. If original PDF is within limit, returns original content

    Raises:
        ValueError: If page_limit is less than or equal to 0
        ValueError: If file_content is not a valid base64 encoded PDF
    """
    if page_limit <= 0:
        raise ValueError("Page limit must be greater than 0")

    try:
        # Decode Base64 string to bytes
        pdf_bytes = base64.b64decode(file_content)
    except Exception as e:
        raise ValueError(f"Invalid base64 content: {str(e)}")

    try:
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as e:
        raise ValueError(f"Invalid PDF content: {str(e)}")

    total_pages = len(pdf_reader.pages)

    if total_pages <= page_limit:
        return file_content  # Return original Base64 string if within limit

    pages_per_section = page_limit // 2
    pdf_writer = PdfWriter()

    # Add first N/2 pages
    for page_num in range(pages_per_section):
        pdf_writer.add_page(pdf_reader.pages[page_num])

    # Add last N/2 pages
    for page_num in range(total_pages - pages_per_section, total_pages):
        pdf_writer.add_page(pdf_reader.pages[page_num])

    # Save the shortened PDF to bytes and encode back to Base64
    output_pdf = io.BytesIO()
    pdf_writer.write(output_pdf)
    processed_bytes = output_pdf.getvalue()
    return base64.b64encode(processed_bytes).decode("utf-8")
