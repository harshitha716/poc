from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime


class Address(BaseModel):
    address1: str
    city: str
    region: str
    postalCode: str
    country: str


class DomesticWireRoutingInfo(BaseModel):
    bankName: str
    accountNumber: str
    routingNumber: str
    address: Address


class TransactionDetails(BaseModel):
    domesticWireRoutingInfo: Optional[DomesticWireRoutingInfo] = None


class Transaction(BaseModel):
    id: str
    feeId: Optional[str]
    amount: float
    createdAt: datetime
    postedAt: Optional[datetime]
    estimatedDeliveryDate: Optional[datetime]
    status: str
    note: Optional[str]
    bankDescription: Optional[str]
    externalMemo: Optional[str]
    counterpartyId: str
    details: TransactionDetails
    reasonForFailure: Optional[str]
    failedAt: Optional[datetime]
    dashboardLink: Optional[str]
    counterpartyName: Optional[str]
    counterpartyNickname: Optional[str]
    kind: str
    currencyExchangeInfo: Optional[Dict[str, Any]]
    compliantWithReceiptPolicy: bool
    hasGeneratedReceipt: bool
    creditAccountPeriodId: Optional[str]
    mercuryCategory: Optional[str]
    generalLedgerCodeName: Optional[str]
    attachments: List[Any]
    relatedTransactions: List[Any]


class CreateTransactionRequest(BaseModel):
    account_id: str = Field(..., description="Mercury account ID")
    recipient_id: str = Field(..., description="ID of the recipient")
    amount: float = Field(..., description="Amount to transfer")
    payment_method: str = Field(
        ..., description="Payment method (e.g., 'domesticWire')"
    )
    idempotency_key: str = Field(
        ..., description="Unique identifier for the transaction"
    )


class GetTransactionParams(BaseModel):
    account_id: str = Field(..., description="Mercury account ID")
    transaction_id: str = Field(..., description="Transaction ID to retrieve")
