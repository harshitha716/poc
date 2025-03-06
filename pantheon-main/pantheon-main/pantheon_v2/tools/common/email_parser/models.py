from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class EmailAddress(BaseModel):
    name: Optional[str] = Field(None, description="Display name of the email address")
    email: str = Field(..., description="Email address")


class Attachment(BaseModel):
    filename: str = Field(..., description="Name of the attachment file")
    content_type: str = Field(..., description="MIME type of the attachment")
    size: int = Field(..., description="Size of the attachment in bytes")
    content: Optional[bytes] = Field(None, description="Raw content of the attachment")


class ParsedEmail(BaseModel):
    subject: Optional[str] = Field(None, description="Email subject")
    from_: EmailAddress = Field(..., alias="from", description="Sender's email address")
    reply_to: List[EmailAddress] = Field(
        default_factory=list, description="Reply-To email addresses"
    )
    to: List[EmailAddress] = Field(
        default_factory=list, description="Recipients' email addresses"
    )
    cc: List[EmailAddress] = Field(default_factory=list, description="CC recipients")
    bcc: List[EmailAddress] = Field(default_factory=list, description="BCC recipients")
    date: Optional[str] = Field(None, description="Email date")
    body_plain: Optional[str] = Field(None, description="Plain text body")
    body_html: Optional[str] = Field(None, description="HTML body")
    attachments: List[Attachment] = Field(
        default_factory=list, description="Email attachments"
    )
    headers: Dict[str, str] = Field(default_factory=dict, description="Email headers")


class ParseEmailParams(BaseModel):
    eml_content: str = Field(..., description="Raw EML content as string")
    include_attachments: bool = Field(
        default=False,
        description="Whether to include attachment contents in the response",
    )
