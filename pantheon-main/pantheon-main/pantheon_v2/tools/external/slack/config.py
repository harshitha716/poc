from pydantic import BaseModel, Field


class SlackConfig(BaseModel):
    api_base_url: str = Field(..., description="Base URL for Slack API")
    api_token: str = Field(..., description="API token for authentication")
