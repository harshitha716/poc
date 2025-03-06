from pydantic import BaseModel


class LLMMessageResponse(BaseModel):
    role: str
    content: str
