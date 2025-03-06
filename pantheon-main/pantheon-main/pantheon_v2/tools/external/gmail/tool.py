import structlog
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json
from base64 import urlsafe_b64decode
from email.utils import parsedate_to_datetime
import base64

from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.core.tool_registry import ToolRegistry
from pantheon_v2.tools.external.gmail.config import GmailConfig
from pantheon_v2.tools.external.gmail.constants import GMAIL_SCOPES
from pantheon_v2.tools.external.gmail.models import (
    GmailSearchParams,
    GmailResponse,
    GmailMessage,
    GmailAttachment,
    GmailGetMessageParams,
)

logger = structlog.get_logger(__name__)


@ToolRegistry.register_tool(
    description="Gmail tool for sending and managing email communications"
)
class GmailTool(BaseTool):
    def __init__(self, config: GmailConfig):
        self.service = None
        self.config = config

    async def initialize(self) -> None:
        """Initialize the Gmail client asynchronously"""
        try:
            self.service = await self._get_gmail_service(self.config)
            logger.info("Gmail tool initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Gmail tool", error=str(e))
            raise

    async def _get_gmail_service(self, config: GmailConfig):
        """Initialize Gmail API service using JSON token data directly"""
        try:
            token_data = json.loads(config.token)

            creds = Credentials(
                token=token_data.get("token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri=token_data.get("token_uri"),
                client_id=token_data.get("client_id"),
                client_secret=token_data.get("client_secret"),
                scopes=GMAIL_SCOPES,
            )

            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            service = build("gmail", "v1", credentials=creds)
            return service
        except json.JSONDecodeError:
            logger.error("Invalid JSON in token value")
            raise
        except Exception as e:
            logger.error("Failed to initialize Gmail service", error=str(e))
            raise

    @ToolRegistry.register_tool_action(
        description="Search for Gmail messages with various filters"
    )
    async def search_messages(self, params: GmailSearchParams) -> GmailResponse:
        """Search for Gmail messages matching the query"""
        try:
            # Build the initial search request
            search_request = {
                "q": params.query,
                "maxResults": params.max_results,
            }

            if params.page_token:
                search_request["pageToken"] = params.page_token

            if params.label_ids:
                search_request["labelIds"] = params.label_ids

            # Execute the search
            results = (
                self.service.users()
                .messages()
                .list(userId="me", **search_request)
                .execute()
            )

            messages = []
            for msg in results.get("messages", []):
                # Get the full message details
                message_data = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="full")
                    .execute()
                )

                # Parse headers
                headers = {
                    header["name"].lower(): header["value"]
                    for header in message_data["payload"]["headers"]
                }

                # Get message body if requested
                body = None
                if params.include_body:
                    body = self._get_message_body(message_data)

                # Get attachments if they exist
                attachments = self._get_attachments(message_data)

                # Create GmailMessage object
                message = GmailMessage(
                    id=message_data["id"],
                    thread_id=message_data["threadId"],
                    subject=headers.get("subject"),
                    sender=headers.get("from"),
                    recipient=headers.get("to"),
                    date=parsedate_to_datetime(headers.get("date")),
                    snippet=message_data["snippet"],
                    body=body,
                    attachments=attachments,
                )
                messages.append(message)

            return GmailResponse(
                messages=messages,
                next_page_token=results.get("nextPageToken"),
                result_size_estimate=results.get("resultSizeEstimate", 0),
            )

        except Exception as e:
            raise Exception(f"Failed to search Gmail messages: {str(e)}")

    def _get_message_body(self, message_data):
        """Extract message body from the message data"""
        if "parts" in message_data["payload"]:
            for part in message_data["payload"]["parts"]:
                if part["mimeType"] == "text/plain":
                    body_data = part["body"].get("data")
                    if body_data:
                        return urlsafe_b64decode(body_data).decode()
        elif "body" in message_data["payload"]:
            body_data = message_data["payload"]["body"].get("data")
            if body_data:
                return urlsafe_b64decode(body_data).decode()
        return None

    def _get_attachments(self, message_data):
        """Extract attachments from the message data"""
        attachments = []
        if "parts" in message_data["payload"]:
            for part in message_data["payload"]["parts"]:
                if part.get("filename"):
                    attachment = GmailAttachment(
                        attachment_id=part["body"].get("attachmentId", ""),
                        filename=part["filename"],
                        mime_type=part["mimeType"],
                        size=int(part["body"].get("size", 0)),
                    )
                    attachments.append(attachment)
        return attachments

    @ToolRegistry.register_tool_action(
        description="Get a specific Gmail message EML content by its ID"
    )
    async def get_message_eml(self, params: GmailGetMessageParams) -> bytes:
        """Retrieve a specific Gmail message in EML format using its message ID"""
        try:
            # Get the raw message data
            message_data = (
                self.service.users()
                .messages()
                .get(userId="me", id=params.message_id, format="raw")
                .execute()
            )

            # Decode the raw message data from base64url to bytes
            eml_data = base64.urlsafe_b64decode(message_data["raw"])
            return eml_data

        except Exception as e:
            raise Exception(f"Failed to get Gmail message: {str(e)}")
