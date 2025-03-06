import uuid
from pydantic import BaseModel, NonNegativeInt


class PageRequest(BaseModel):
    page_id: uuid.UUID
    sheet_id: NonNegativeInt


class ChatRequest(BaseModel):
    query: str
    page_request: PageRequest


class ChatResponse(BaseModel):
    status: str
    action: str
    content: str
    explanation: str


class ChatTransformationResponse(BaseModel):
    status: str
    action: str
