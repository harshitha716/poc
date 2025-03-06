import pytest
from unittest.mock import MagicMock

from pantheon_v2.tools.common.email_parser.tool import EmailParserTool
from pantheon_v2.tools.common.email_parser.models import (
    ParseEmailParams,
    EmailAddress,
)


@pytest.fixture
def tool():
    """Create a mock tool with required configuration"""
    tool = EmailParserTool(config={})
    tool.config = MagicMock()
    tool.config.max_size = 1024 * 1024  # 1MB
    return tool


@pytest.fixture
def sample_email():
    return """From: John Doe <john@example.com>
To: Jane Smith <jane@example.com>, Bob Wilson <bob@example.com>
Cc: team@example.com
Subject: Test Email
Date: Thu, 1 Apr 2024 12:00:00 -0000
Content-Type: multipart/mixed; boundary="boundary123"

--boundary123
Content-Type: text/plain

Hello, this is a test email.
--boundary123
Content-Type: text/html

<html><body><p>Hello, this is a test email.</p></body></html>
--boundary123
Content-Type: application/pdf; name="test.pdf"
Content-Disposition: attachment; filename="test.pdf"
Content-Transfer-Encoding: base64

SGVsbG8gV29ybGQ=
--boundary123--"""


class TestEmailParserActions:
    def test_parse_address(self, tool):
        """Test parsing of email addresses"""
        # Test valid email address with name
        result = tool._parse_address("John Doe <john@example.com>")
        assert result == EmailAddress(name="John Doe", email="john@example.com")

        # Test email address without name
        result = tool._parse_address("john@example.com")
        assert result == EmailAddress(name=None, email="john@example.com")

        # Test invalid email address
        result = tool._parse_address("")
        assert result == EmailAddress(name=None, email="unknown@example.com")

    def test_parse_address_list(self, tool):
        """Test parsing of email address lists"""
        addr_list = "John Doe <john@example.com>, jane@example.com"
        result = tool._parse_address_list(addr_list)
        assert len(result) == 2
        assert result[0] == EmailAddress(name="John Doe", email="john@example.com")
        assert result[1] == EmailAddress(name=None, email="jane@example.com")

    async def test_parse_email(self, tool, sample_email):
        """Test parsing a complete email"""
        params = ParseEmailParams(eml_content=sample_email, include_attachments=True)
        result = await tool.parse_email(params)

        # Check basic fields
        assert result.subject == "Test Email"
        assert result.from_.email == "john@example.com"
        assert result.from_.name == "John Doe"

        # Check recipients
        assert len(result.to) == 2
        assert result.to[0].email == "jane@example.com"
        assert len(result.cc) == 1
        assert result.cc[0].email == "team@example.com"

        # Check content
        assert "Hello, this is a test email." in result.body_plain
        assert "<p>Hello, this is a test email.</p>" in result.body_html

        # Check attachment
        assert len(result.attachments) == 1
        assert result.attachments[0].filename == "test.pdf"
        assert result.attachments[0].content_type == "application/pdf"

    async def test_email_size_limit(self, tool):
        """Test email size limit enforcement"""
        large_content = "x" * (1024 * 1024 + 1)  # Exceeds 1MB
        params = ParseEmailParams(eml_content=large_content, include_attachments=False)

        with pytest.raises(ValueError, match="Email content exceeds maximum size"):
            await tool.parse_email(params)

    def test_process_attachment(self, tool):
        """Test attachment processing"""
        from email.message import EmailMessage

        # Create a test attachment
        msg = EmailMessage()
        msg.set_content("test content")
        msg.add_attachment(
            b"test content", maintype="application", subtype="pdf", filename="test.pdf"
        )

        for part in msg.iter_attachments():
            attachment = tool._process_attachment(part, include_content=True)
            assert attachment.filename == "test.pdf"
            assert attachment.content_type == "application/pdf"
            assert attachment.size > 0
            assert attachment.content is not None

    async def test_parse_email_with_reply_to(self, tool):
        """Test parsing email with reply-to header"""
        email_content = """From: John Doe <john@example.com>
Reply-To: support@example.com, backup@example.com
Subject: Test Email
Content-Type: text/plain

Test content"""

        params = ParseEmailParams(eml_content=email_content, include_attachments=False)
        result = await tool.parse_email(params)

        assert len(result.reply_to) == 2
        assert result.reply_to[0].email == "support@example.com"
        assert result.reply_to[1].email == "backup@example.com"

    async def test_parse_email_with_different_encodings(self, tool):
        """Test parsing email with different character encodings"""
        email_content = """From: =?UTF-8?Q?Jos=C3=A9_Garc=C3=ADa?= <jose@example.com>
To: =?UTF-8?Q?Andr=C3=A9_Martin?= <andre@example.com>
Subject: Test Subject
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

Content with special characters: =C3=A1=C3=A9=C3=AD=C3=B3=C3=BA"""

        params = ParseEmailParams(eml_content=email_content, include_attachments=False)
        result = await tool.parse_email(params)

        assert result.from_.name == "José García"
        assert "áéíóú" in result.body_plain.strip()

    def test_parse_malformed_address(self, tool):
        """Test parsing malformed email addresses"""
        test_cases = [
            (
                "Invalid Email",
                EmailAddress(name=None, email="Invalid"),
            ),  # parseaddr keeps the text as email part
            ("missing@domain", EmailAddress(name=None, email="missing@domain")),
            (
                "@nodomain.com",
                EmailAddress(name=None, email="@nodomain.com"),
            ),  # parseaddr keeps the invalid email
            (
                "spaces in@email.com",
                EmailAddress(name=None, email="spaces in@email.com"),
            ),  # parseaddr keeps the invalid email
            (
                "<incomplete@email.com",
                EmailAddress(name=None, email="incomplete@email.com"),
            ),
            (
                "",
                EmailAddress(name=None, email="unknown@example.com"),
            ),  # empty string returns default
            (
                None,
                EmailAddress(name=None, email="unknown@example.com"),
            ),  # None returns default
        ]

        for input_addr, expected_result in test_cases:
            result = tool._parse_address(input_addr)
            assert (
                result == expected_result
            ), f"Failed for address: {input_addr}\nExpected: {expected_result}\nGot: {result}"

    async def test_parse_email_with_invalid_date(self, tool):
        """Test parsing email with invalid date format"""
        email_content = """From: test@example.com
Date: Invalid Date Format
Subject: Test

Content"""

        params = ParseEmailParams(eml_content=email_content, include_attachments=False)
        result = await tool.parse_email(params)

        # The email.message.EmailMessage class keeps the raw date string
        # if it can't parse it, so we should check the raw value
        assert result.date == "Invalid Date Format"

    async def test_parse_email_headers_case_insensitive(self, tool):
        """Test that header parsing is case-insensitive"""
        email_content = """FROM: test@example.com
SUBJECT: Test Subject
To: recipient@example.com
CC: cc@example.com
Content-type: text/plain

Content"""

        params = ParseEmailParams(eml_content=email_content, include_attachments=False)
        result = await tool.parse_email(params)

        assert result.from_.email == "test@example.com"
        assert result.subject == "Test Subject"
        assert result.to[0].email == "recipient@example.com"
        assert result.cc[0].email == "cc@example.com"
