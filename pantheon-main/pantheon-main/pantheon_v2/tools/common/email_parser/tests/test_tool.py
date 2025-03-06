import pytest
from pantheon_v2.tools.common.email_parser.tool import EmailParserTool
from pantheon_v2.tools.common.email_parser.config import EmailParserConfig


@pytest.fixture
def email_parser_tool():
    config = EmailParserConfig(max_size=1024 * 1024)
    return EmailParserTool(config)


async def test_tool_initialization(email_parser_tool):
    """Test that the tool initializes successfully"""
    await email_parser_tool.initialize()
    assert email_parser_tool.config.max_size == 1024 * 1024
