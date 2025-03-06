import structlog
import email
from email import policy
from email.message import EmailMessage
from email.utils import parseaddr
from typing import List

from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.common.email_parser.config import EmailParserConfig
from pantheon_v2.tools.common.email_parser.models import (
    ParseEmailParams,
    ParsedEmail,
    EmailAddress,
    Attachment,
)

from pantheon_v2.tools.core.tool_registry import ToolRegistry

logger = structlog.get_logger(__name__)


@ToolRegistry.register_tool(
    description="Tool for parsing email (EML) files and extracting their contents"
)
class EmailParserTool(BaseTool):
    def __init__(self, config: EmailParserConfig):
        self.config = config

    async def initialize(self) -> None:
        """Initialize the email parser tool"""
        try:
            logger.info("Email parser tool initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize email parser tool", error=str(e))
            raise

    @ToolRegistry.register_tool_action(
        description="Parse an email string and extract its contents"
    )
    async def parse_email(self, params: ParseEmailParams) -> ParsedEmail:
        """Parse EML content and extract its contents"""
        try:
            if len(params.eml_content) > self.config.max_size:
                raise ValueError(
                    f"Email content exceeds maximum size of {self.config.max_size} bytes"
                )

            # Parse with policy to handle modern email features
            msg = email.message_from_string(params.eml_content, policy=policy.default)

            # Extract email parts
            body_plain = None
            body_html = None
            attachments = []

            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue

                content_type = part.get_content_type()

                # Handle attachments
                if part.get_filename():
                    attachment = self._process_attachment(
                        part, params.include_attachments
                    )
                    attachments.append(attachment)
                # Handle text parts
                elif content_type == "text/plain":
                    body_plain = part.get_content()
                elif content_type == "text/html":
                    body_html = part.get_content()

            # Parse addresses with better error handling
            from_header = msg.get("from", "")
            from_address = self._parse_address(from_header)

            to_addresses = self._parse_address_list(msg.get("to", ""))
            cc_addresses = self._parse_address_list(msg.get("cc", ""))
            bcc_addresses = self._parse_address_list(msg.get("bcc", ""))

            # Add reply-to parsing
            reply_to_addresses = self._parse_address_list(msg.get("reply-to", ""))

            parsed_email = ParsedEmail(
                subject=msg.get("subject"),
                **{"from": from_address},
                reply_to=reply_to_addresses,
                to=to_addresses,
                cc=cc_addresses,
                bcc=bcc_addresses,
                date=msg.get("date"),
                body_plain=body_plain,
                body_html=body_html,
                attachments=attachments,
                headers={k: str(v) for k, v in msg.items()},
            )

            return parsed_email

        except Exception as e:
            logger.error(
                "Failed to parse email",
                error=str(e),
                from_address=from_address if "from_address" in locals() else None,
            )
            raise

    def _parse_address(self, addr_string: str) -> EmailAddress:
        """Parse email address string into name and email components"""
        if not addr_string:
            return EmailAddress(name=None, email="unknown@example.com")
        try:
            name, email_addr = parseaddr(addr_string)
            if not email_addr:  # If parsing fails
                return EmailAddress(name=None, email="unknown@example.com")
            return EmailAddress(name=name or None, email=email_addr)
        except Exception as e:
            logger.error(
                "Failed to parse email address", error=str(e), addr_string=addr_string
            )
            return EmailAddress(name=None, email="unknown@example.com")

    def _parse_address_list(self, addr_list: str) -> List[EmailAddress]:
        """Parse comma-separated email addresses"""
        if not addr_list:
            return []
        addresses = addr_list.split(",")
        return [self._parse_address(addr.strip()) for addr in addresses if addr.strip()]

    def _process_attachment(
        self, part: EmailMessage, include_content: bool
    ) -> Attachment:
        """Process email attachment with better content type handling"""
        filename = part.get_filename()
        content_type = part.get_content_type()
        content = part.get_payload(decode=True)

        # Handle base64 encoded PDF attachments
        if (
            content_type == "application/pdf"
            and part.get("Content-Transfer-Encoding") == "base64"
        ):
            try:
                content = part.get_payload(decode=True)
            except Exception as e:
                logger.error("Failed to decode PDF attachment", error=str(e))
                content = None

        return Attachment(
            filename=filename,
            content_type=content_type,
            size=len(content) if content else 0,
            content=content if include_content else None,
        )
