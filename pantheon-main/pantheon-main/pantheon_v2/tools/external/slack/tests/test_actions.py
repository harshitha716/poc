import pytest
from unittest.mock import patch
import structlog

from pantheon_v2.tools.external.slack.tool import SlackTool
from pantheon_v2.tools.external.slack.config import SlackConfig
from pantheon_v2.tools.external.slack.models import (
    SlackMessageRequest,
    SlackMessageResponse,
)
from pantheon_v2.tools.external.slack.constants import API_ENDPOINT, DEFAULT_HEADERS
from pantheon_v2.utils.api_client import ApiClient, HttpMethod

logger = structlog.get_logger(__name__)


@pytest.fixture
def mock_config():
    """Create a mock Slack configuration"""
    return SlackConfig(
        api_base_url="https://api.example.com", api_token="test-token-123"
    )


@pytest.fixture
def mock_request():
    """Create a mock Slack message request"""
    return SlackMessageRequest(
        message_data={
            "workflow_id": "test-workflow-123",
            "run_id": "run-123",
            "vendor": "Test Vendor",
            "user_email": "test@example.com",
            "invoice_id": "INV-123",
            "invoice_date": "2024-03-15",
            "invoice_amount": "1000.00",
            "due_date": "2024-04-15",
            "description": "Test invoice",
            "invoice_gcs_path": "gs://bucket/path/to/invoice.pdf",
        },
    )


@pytest.fixture
def slack_tool(mock_config):
    """Create a Slack tool instance with mocked config"""
    return SlackTool(config=mock_config)


class TestSlackTool:
    async def test_initialization(self, slack_tool):
        """Test successful tool initialization"""
        await slack_tool.initialize()
        assert slack_tool.config.api_base_url == "https://api.example.com"
        assert slack_tool.config.api_token == "test-token-123"
        assert isinstance(slack_tool.client, ApiClient)

    async def test_initialization_with_invalid_config(self):
        """Test initialization with invalid configuration"""
        with pytest.raises(ValueError):
            SlackConfig(api_base_url=None, api_token=None)

    @patch.object(ApiClient, "request")
    async def test_send_message_success(
        self, mock_request_method, slack_tool, mock_request
    ):
        """Test successful message sending"""
        mock_response = SlackMessageResponse(status="success")
        mock_request_method.return_value = mock_response

        response = await slack_tool.send_message(mock_request)

        mock_request_method.assert_called_once_with(
            method=HttpMethod.POST,
            endpoint=API_ENDPOINT,
            response_model=SlackMessageResponse,
            data=mock_request.message_data,
            params={"token": slack_tool.config.api_token},
        )
        assert response.status == "success"

    @patch.object(ApiClient, "request")
    async def test_send_message_with_minimal_params(
        self, mock_request_method, slack_tool
    ):
        """Test sending message with only required parameters"""
        minimal_request = SlackMessageRequest(
            workflow_id="test-workflow",
            run_id="run-123",
            message_data={
                "vendor": "Test Vendor",
                "user_email": "test@example.com",
                "invoice_id": "INV-123",
                "invoice_date": "2024-03-15",
                "invoice_amount": "1000.00",
            },
        )

        mock_response = SlackMessageResponse(status="success")
        mock_request_method.return_value = mock_response

        response = await slack_tool.send_message(minimal_request)
        assert response.status == "success"
        mock_request_method.assert_called_once()

    @patch.object(ApiClient, "request")
    async def test_send_message_api_error(
        self, mock_request_method, slack_tool, mock_request
    ):
        """Test handling of API errors"""
        mock_request_method.side_effect = Exception("API Error")

        with pytest.raises(Exception) as exc_info:
            await slack_tool.send_message(mock_request)
        assert "API Error" in str(exc_info.value)

    async def test_client_headers(self, slack_tool):
        """Test API client is configured with correct headers"""
        assert slack_tool.client.default_headers == DEFAULT_HEADERS
        assert slack_tool.client.default_headers["Content-Type"] == "application/json"
        assert slack_tool.client.default_headers["Accept"] == "application/json"

    @patch.object(ApiClient, "request")
    async def test_send_message_with_special_characters(
        self, mock_request_method, slack_tool
    ):
        """Test sending message with special characters"""
        request = SlackMessageRequest(
            workflow_id="test-workflow-123",
            run_id="run-123",
            message_data={
                "vendor": "Test & Vendor's Corp.",
                "user_email": "test+special@example.com",
                "invoice_id": "INV#123",
                "invoice_date": "2024-03-15",
                "invoice_amount": "1,000.00",
                "description": "Test & special chars: @#$%",
            },
        )

        mock_response = SlackMessageResponse(status="success")
        mock_request_method.return_value = mock_response

        response = await slack_tool.send_message(request)
        assert response.status == "success"
        mock_request_method.assert_called_once()

    @patch.object(ApiClient, "request")
    async def test_send_message_with_long_content(
        self, mock_request_method, slack_tool
    ):
        """Test sending message with long content"""
        long_description = "x" * 1000  # Create a 1000-character string
        request = SlackMessageRequest(
            workflow_id="test-workflow-123",
            run_id="run-123",
            message_data={
                "vendor": "Test Vendor",
                "user_email": "test@example.com",
                "invoice_id": "INV-123",
                "invoice_date": "2024-03-15",
                "invoice_amount": "1000.00",
                "description": long_description,
            },
        )

        mock_response = SlackMessageResponse(status="success")
        mock_request_method.return_value = mock_response

        response = await slack_tool.send_message(request)
        assert response.status == "success"
        mock_request_method.assert_called_once()

    @patch.object(ApiClient, "request")
    async def test_send_message_retry_behavior(
        self, mock_request_method, slack_tool, mock_request
    ):
        """Test retry behavior on temporary failure"""
        mock_request_method.side_effect = [
            Exception("Temporary failure"),
            SlackMessageResponse(status="success"),
        ]

        with pytest.raises(Exception):
            await slack_tool.send_message(mock_request)

    @patch.object(ApiClient, "request")
    async def test_send_message_invalid_dates(self, mock_request_method, slack_tool):
        """Test handling of invalid date formats"""
        request = SlackMessageRequest(
            workflow_id="test-workflow-123",
            run_id="run-123",
            message_data={
                "vendor": "Test Vendor",
                "user_email": "test@example.com",
                "invoice_id": "INV-123",
                "invoice_date": "invalid-date",  # Invalid date format
                "invoice_amount": "1000.00",
            },
        )

        mock_response = SlackMessageResponse(status="success")
        mock_request_method.return_value = mock_response

        # Should not raise validation error since date validation moved to business logic
        response = await slack_tool.send_message(request)
        assert response.status == "success"
