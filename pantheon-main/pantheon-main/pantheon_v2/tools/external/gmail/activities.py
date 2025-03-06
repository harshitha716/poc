from pantheon_v2.tools.external.gmail.tool import GmailTool
from pantheon_v2.tools.external.gmail.models import (
    GmailSearchParams,
    GmailResponse,
    GmailGetMessageParams,
)
from pantheon_v2.tools.external.gmail.config import GmailConfig
from pantheon_v2.tools.core.activity_registry import ActivityRegistry


@ActivityRegistry.register_activity("Search for Gmail messages with various filters")
async def search_messages(
    config: GmailConfig, params: GmailSearchParams
) -> GmailResponse:
    tool = GmailTool(config)
    await tool.initialize()
    return await tool.search_messages(params)


@ActivityRegistry.register_activity(
    "Get a specific Gmail message EML content by its ID"
)
async def get_message_eml(config: GmailConfig, params: GmailGetMessageParams) -> bytes:
    tool = GmailTool(config)
    await tool.initialize()
    return await tool.get_message_eml(params)
