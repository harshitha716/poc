from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class GmailAttachment(BaseModel):
    attachment_id: str
    filename: str
    mime_type: str
    size: int
    data: Optional[bytes] = None


class GmailMessage(BaseModel):
    id: str = Field(..., min_length=1)
    thread_id: str = Field(..., min_length=1)
    subject: Optional[str] = Field(default=None, min_length=1)
    sender: str = Field(..., min_length=1)
    recipient: str = Field(..., min_length=1)
    date: datetime = Field(..., description="Date of the message")
    snippet: str = Field(..., min_length=1)
    body: Optional[str] = Field(default=None, min_length=1)
    attachments: List[GmailAttachment] = Field(default_factory=list)


class GmailResponse(BaseModel):
    messages: List[GmailMessage]
    next_page_token: Optional[str]
    result_size_estimate: int


class GmailSearchParams(BaseModel):
    query: str = Field(
        ..., description="Gmail search query (e.g., 'from:someone@email.com')"
    )
    max_results: int = Field(
        10, description="Maximum number of results to return", le=500
    )
    page_token: Optional[str] = Field(
        None, description="Token for getting the next page of results"
    )
    include_body: bool = Field(
        False, description="Whether to include full message body"
    )
    label_ids: Optional[List[str]] = Field(
        None, description="Filter by specific Gmail labels"
    )


class GmailGetMessageParams(BaseModel):
    message_id: str = Field(..., description="Gmail message id")
