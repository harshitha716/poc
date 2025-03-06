import pytest
from unittest.mock import MagicMock

from pantheon_v2.tools.external.gmail.tool import GmailTool
from pantheon_v2.tools.external.gmail.models import (
    GmailSearchParams,
    GmailResponse,
    GmailGetMessageParams,
)


@pytest.fixture
def mock_tool():
    tool = GmailTool({})
    tool.service = MagicMock()
    return tool


@pytest.fixture
def actions(mock_tool):
    return mock_tool


class TestGmailActions:
    @pytest.mark.asyncio
    async def test_search_messages_success(self, actions, mock_tool):
        # Mock response data for list call
        mock_list_response = {
            "messages": [{"id": "msg1"}],
            "nextPageToken": "next_token",
            "resultSizeEstimate": 1,
        }

        # Mock response data for get call
        mock_message_data = {
            "id": "msg1",
            "threadId": "thread1",
            "snippet": "Test message",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "sender@test.com"},
                    {"name": "To", "value": "recipient@test.com"},
                    {"name": "Date", "value": "Thu, 1 Jan 2024 00:00:00 +0000"},
                ],
                "parts": [{"mimeType": "text/plain", "body": {"data": "VGVzdCBib2R5"}}],
            },
        }

        # Setup mock service calls
        mock_users = MagicMock()
        mock_messages = MagicMock()
        mock_list = MagicMock()
        mock_get = MagicMock()

        mock_list.execute.return_value = mock_list_response
        mock_get.execute.return_value = mock_message_data

        mock_messages.list.return_value = mock_list
        mock_messages.get.return_value = mock_get
        mock_users.messages.return_value = mock_messages
        mock_tool.service.users.return_value = mock_users

        # Execute search
        params = GmailSearchParams(query="from:someone@email.com", include_body=True)
        result = await actions.search_messages(params)

        # Assertions
        assert isinstance(result, GmailResponse)
        assert len(result.messages) == 1
        assert result.next_page_token == "next_token"
        assert result.result_size_estimate == 1

        # Verify message details
        message = result.messages[0]
        assert message.id == "msg1"
        assert message.thread_id == "thread1"
        assert message.subject == "Test Subject"
        assert message.sender == "sender@test.com"
        assert message.recipient == "recipient@test.com"

    @pytest.mark.asyncio
    async def test_search_messages_no_results(self, actions, mock_tool):
        # Mock empty response
        mock_messages_list = MagicMock()
        mock_messages_list.get.side_effect = lambda key, default=None: {
            "messages": [],
            "nextPageToken": None,
            "resultSizeEstimate": 0,
        }.get(key, default)

        # Setup mock service calls
        mock_messages = MagicMock()
        mock_list = MagicMock()
        mock_list.execute.return_value = mock_messages_list
        mock_messages.list.return_value = mock_list
        mock_tool.service.users.return_value.messages.return_value = mock_messages

        # Execute search
        params = GmailSearchParams(query="nonexistent@email.com")
        result = await actions.search_messages(params)

        # Assertions
        assert isinstance(result, GmailResponse)
        assert len(result.messages) == 0
        assert result.next_page_token is None
        assert result.result_size_estimate == 0

    @pytest.mark.asyncio
    async def test_get_message_eml_success(self, actions, mock_tool):
        # Mock raw message data
        mock_message_data = {
            "raw": "SGVsbG8gV29ybGQ="  # Base64 encoded "Hello World"
        }

        # Setup mock service calls
        mock_users = MagicMock()
        mock_messages = MagicMock()
        mock_get = MagicMock()

        mock_get.execute.return_value = mock_message_data
        mock_messages.get.return_value = mock_get
        mock_users.messages.return_value = mock_messages
        mock_tool.service.users.return_value = mock_users

        # Execute get message
        params = GmailGetMessageParams(message_id="msg1")
        result = await actions.get_message_eml(params)

        # Assertions
        assert isinstance(result, bytes)
        assert result.decode() == "Hello World"

        # Verify the correct API calls were made
        mock_messages.get.assert_called_once_with(userId="me", id="msg1", format="raw")

    @pytest.mark.asyncio
    async def test_get_message_eml_error(self, actions, mock_tool):
        # Setup mock service to raise an error
        mock_messages = MagicMock()
        mock_messages.get.side_effect = Exception("API Error")
        mock_tool.service.users().messages = mock_messages

        # Execute get message and verify error handling
        params = GmailGetMessageParams(message_id="msg1")
        with pytest.raises(Exception) as exc_info:
            await actions.get_message_eml(params)

        assert "Failed to get Gmail message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_messages_error(self, actions, mock_tool):
        # Setup mock service to raise an error
        mock_messages = MagicMock()
        mock_messages.list.side_effect = Exception("API Error")
        mock_tool.service.users().messages = mock_messages

        # Execute search and verify error handling
        params = GmailSearchParams(query="test@email.com")
        with pytest.raises(Exception) as exc_info:
            await actions.search_messages(params)

        assert "Failed to search Gmail messages" in str(exc_info.value)
