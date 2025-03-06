from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class ZampAPAgentWorkflowInput(BaseModel):
    newer_than: str


class VendorByEmailQueryResult(BaseModel):
    id: str


class ProcessedEmailQueryResult(BaseModel):
    message_id: str


class EmailByIdAndStatusQueryResult(BaseModel):
    id: UUID
    message_id: str


class ZampApAgentEmailSchema(BaseModel):
    id: UUID
    message_id: str
    subject: str
    from_email: str = Field(serialization_alias="from", validation_alias="from")
    received_at: datetime
    storage_path: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        populate_by_alias = True
