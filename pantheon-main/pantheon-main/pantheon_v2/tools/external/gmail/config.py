from pydantic import BaseModel, Field
from pantheon_v2.settings.settings import Settings


class GmailConfig(BaseModel):
    token: str = Field(..., description="The token for the Gmail API")


GMAIL_CONFIG = GmailConfig(
    token=Settings.GMAIL_TOKEN,
)
