import pytest
from unittest.mock import MagicMock, patch, ANY
import json

from pantheon_v2.tools.external.gmail.tool import GmailTool
from pantheon_v2.tools.external.gmail.config import GmailConfig


@pytest.fixture
def gmail_config():
    return GmailConfig(
        token=json.dumps(
            {
                "token": "test_token",
                "refresh_token": "test_refresh_token",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            }
        )
    )


@pytest.fixture
def gmail_tool(gmail_config):
    return GmailTool(config=gmail_config)


class TestGmailTool:
    @pytest.mark.asyncio
    async def test_initialize_success(self, gmail_tool):
        """Test successful initialization of GmailTool"""
        with patch("pantheon_v2.tools.external.gmail.tool.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service

            await gmail_tool.initialize()

            # Verify service creation using ANY instead of pytest.any()
            mock_build.assert_called_once_with("gmail", "v1", credentials=ANY)
            assert gmail_tool.service == mock_service

    @pytest.mark.asyncio
    async def test_initialize_failure_service_error(self, gmail_tool):
        """Test initialization failure when service creation fails"""
        with patch(
            "pantheon_v2.tools.external.gmail.tool.build",
            side_effect=Exception("Service Error"),
        ):
            with pytest.raises(Exception) as exc_info:
                await gmail_tool.initialize()

            assert str(exc_info.value) == "Service Error"
