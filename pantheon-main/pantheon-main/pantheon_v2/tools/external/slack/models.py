from typing import Dict, Any
from pydantic import BaseModel


class SlackMessageRequest(BaseModel):
    message_data: Dict[str, Any]


class SlackMessageResponse(BaseModel):
    status: str
