from pydantic import BaseModel, Field
from typing import List, Type
from enum import Enum
from pantheon_v2.core.common.generic_base_model import GenericBaseModel


class FileContent(BaseModel):
    file_content: str
    file_type: str
    file_url: str
    content_type: str


class ExtractionType(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"


class OCRExtractInput(BaseModel):
    file_content: List[str]  # Array of Base64 encoded file contents
    extract_dto: Type[BaseModel] = None  # Change to accept the class type
    extraction_type: ExtractionType = None


class OCRExtractOutput[T: BaseModel](GenericBaseModel):
    extracted_data: T  # The extracted data in the DTO format


class InvoiceData(BaseModel):
    is_invoice: bool = Field(
        description="Boolean flag indicating whether the document is an invoice"
    )
    confidence: float = Field(
        description="Confidence score of the extraction (0.0 to 1.0)"
    )
    bill_to_name: str = Field(
        description="Name of the company or individual being billed"
    )
    bill_to_address: str = Field(
        description="Complete billing address of the recipient"
    )
    bill_from_name: str = Field(
        description="Name of the vendor/company issuing the invoice"
    )
    bill_from_address: str = Field(description="Complete address of the vendor/company")
    currency: str = Field(
        description="Three-letter currency code (e.g., USD, EUR, GBP)"
    )
    invoice_number: str = Field(description="Unique identifier for the invoice")
    issue_date: str = Field(
        description="Date when the invoice was issued (YYYY-MM-DD format)"
    )
    due_date: str = Field(
        description="Date when the payment is due (YYYY-MM-DD format)"
    )
    total_amount: float = Field(
        description="Total amount to be paid, including all taxes and fees"
    )
    itemized_breakdown: str = Field(
        description="Detailed breakdown of charges including subtotal, taxes, fees, etc."
    )
    description: str = Field(
        description="Brief description of the products or services being billed"
    )
