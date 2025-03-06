from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime


class APInvoiceApprovalWorkflowInput(BaseModel):
    invoice_id: str


class APInvoiceApprovalWorkflowOutput(BaseModel):
    invoice_id: str
    status: str


class ApprovalState(BaseModel):
    current_approver: str
    approval_chain: list[str]
    current_level: int
    is_completed: bool


class InvoiceData(BaseModel):
    is_invoice: bool
    confidence: float
    bill_to_name: str
    bill_to_address: str
    bill_from_name: str
    bill_from_address: str
    currency: str
    invoice_number: str
    issue_date: str
    due_date: str
    total_amount: float
    itemized_breakdown: str
    description: str


class ProcessedFileInfo(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda dt: dt.isoformat()},
    )

    name: str
    full_path: str
    relative_path: str
    size: int
    content_type: str
    created: datetime
    updated: datetime
    extracted_data: Optional[InvoiceData] = None
    error: Optional[str] = None


class FetchHierarchyResponse(BaseModel):
    next_approver: str
    vendor_id: str
    invoice_date: str
    invoice_amount: str
    due_date: Optional[str]
    description: str
    invoice_gcs_path: Optional[str]


class ApprovalResponse(BaseModel):
    code: str
    message: str
    status: Literal["approve", "disapprove"]


class ApprovalActivityResponse(BaseModel):
    next_approver: Optional[str]
    should_continue: bool
    msg: Optional[str]
    status: Literal["approve", "disapprove"]


class FetchInvoiceQueryResult(BaseModel):
    approvers: List[Dict[str, Any]]
    gcspath: str


class FetchHierarchyQueryResult(BaseModel):
    id: str
    vendorid: str
    amount: str
    invoicedate: Optional[str]
    duedate: Optional[str]
    status: Optional[str]
    approvers: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    description: str
    invoice_gcs_path: Optional[str]


class FetchInvoiceMetadataQueryResult(BaseModel):
    metadata: Dict[str, Any]


class ZampApAgentInvoicesSchema(BaseModel):
    id: str
    vendorid: str
    gcspath: str
    status: str
