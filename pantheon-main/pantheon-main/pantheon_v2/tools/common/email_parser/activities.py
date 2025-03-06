from pantheon_v2.tools.common.email_parser.tool import EmailParserTool
from pantheon_v2.tools.common.email_parser.config import EmailParserConfig
from pantheon_v2.tools.common.email_parser.models import (
    ParseEmailParams,
    ParsedEmail,
)

from pantheon_v2.tools.core.activity_registry import ActivityRegistry


@ActivityRegistry.register_activity("Parse email content and extract its contents")
async def parse_email(
    config: EmailParserConfig, params: ParseEmailParams
) -> ParsedEmail:
    """Parse email content and extract its contents"""
    tool = EmailParserTool(config)
    await tool.initialize()
    return await tool.parse_email(params)
