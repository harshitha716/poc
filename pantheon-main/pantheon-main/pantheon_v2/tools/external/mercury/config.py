from pydantic import BaseModel, Field


class MercuryConfig(BaseModel):
    api_key: str = Field(..., description="Mercury API key")
