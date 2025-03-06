from pydantic import BaseModel, Field


class TestModel(BaseModel):
    invoice_number: str = Field(default="invoice number from the document")  # type: ignore
    invoice_status: str = Field(
        default="invoice status from the document. Use 'PROCESSED' by default"
    )
