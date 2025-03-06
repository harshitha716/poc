import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import tempfile
import shutil
from io import BytesIO

from pantheon_v2.tools.external.s3.activities import (
    download_from_s3,
    upload_to_s3,
    download_folder_from_s3,
    get_internal_s3_config,
)
from pantheon_v2.tools.external.s3.models import (
    DownloadFromS3Input,
    UploadToS3Input,
    DownloadFolderFromS3Input,
)


@pytest.fixture
def mock_settings():
    with patch("pantheon_v2.tools.external.s3.activities.Settings") as mock_settings:
        mock_settings.AWS_ACCESS_KEY_ID = "test_key"
        mock_settings.AWS_SECRET_ACCESS_KEY = "test_secret"
        yield mock_settings


@pytest.fixture
def mock_s3_tool():
    with patch("pantheon_v2.tools.external.s3.activities.S3Tool") as mock_tool_class:
        mock_tool = AsyncMock()
        mock_tool_class.return_value = mock_tool
        yield mock_tool


class TestS3Activities:
    @pytest.fixture
    def mock_settings(self):
        """Mock the Settings class with proper string values for AWS credentials"""
        with patch(
            "pantheon_v2.tools.external.s3.activities.Settings"
        ) as mock_settings:
            # Set attributes as string values, not MagicMock objects
            mock_settings.AWS_ACCESS_KEY_ID = "test_access_key"
            mock_settings.AWS_SECRET_ACCESS_KEY = "test_secret_key"
            mock_settings.AWS_REGION = "us-east-1"
            yield mock_settings

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing file operations"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Clean up after the test
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_s3_tool(self):
        """Mock the S3Tool to prevent actual AWS calls"""
        with patch("pantheon_v2.tools.external.s3.activities.S3Tool") as MockTool:
            mock_tool_instance = MockTool.return_value
            mock_tool_instance.initialize = AsyncMock()
            mock_tool_instance.download_from_s3 = AsyncMock()
            mock_tool_instance.upload_to_s3 = AsyncMock()
            mock_tool_instance.download_folder_from_s3 = AsyncMock()
            yield mock_tool_instance

    def test_get_internal_s3_config(self, mock_settings):
        """Test getting internal S3 configuration"""
        config = get_internal_s3_config()
        assert config.aws_access_key == "test_access_key"
        assert config.aws_secret_key == "test_secret_key"
        assert config.region_name == "us-east-1"

    @pytest.mark.asyncio
    async def test_download_from_s3(self, mock_s3_tool):
        """Test the download_from_s3 activity"""
        # Set up input parameters
        input_params = DownloadFromS3Input(
            bucket_name="test-bucket",
            file_name="test/path/file.txt",
        )

        # Mock successful download
        mock_output = MagicMock()
        mock_s3_tool.download_from_s3.return_value = mock_output

        # Call the activity
        result = await download_from_s3(input_params)

        # Verify tool was initialized
        mock_s3_tool.initialize.assert_called_once()

        # Verify download_from_s3 was called with correct parameters
        mock_s3_tool.download_from_s3.assert_called_once_with(input_params)

        # Verify result
        assert result == mock_output

    @pytest.mark.asyncio
    async def test_upload_to_s3(self, mock_s3_tool):
        """Test the upload_to_s3 activity"""
        # Create BytesIO object
        file_content = BytesIO(b"Test content")

        # Set up input parameters
        input_params = UploadToS3Input(
            bucket_name="test-bucket",
            file_name="test/path/uploaded_file.txt",
            blob=file_content,
            content_type="text/plain",
        )

        # Mock successful upload
        mock_output = MagicMock()
        mock_s3_tool.upload_to_s3.return_value = mock_output

        # Call the activity
        result = await upload_to_s3(input_params)

        # Verify tool was initialized
        mock_s3_tool.initialize.assert_called_once()

        # Verify upload_to_s3 was called with correct parameters
        mock_s3_tool.upload_to_s3.assert_called_once_with(input_params)

        # Verify result
        assert result == mock_output

    @pytest.mark.asyncio
    async def test_download_folder_from_s3(self, mock_s3_tool):
        """Test the download_folder_from_s3 activity"""
        # Set up input parameters
        input_params = DownloadFolderFromS3Input(
            bucket_name="test-bucket",
            folder_path="test/folder/",
        )

        # Mock successful folder download
        mock_output = MagicMock()
        mock_s3_tool.download_folder_from_s3.return_value = mock_output

        # Call the activity
        result = await download_folder_from_s3(input_params)

        # Verify tool was initialized
        mock_s3_tool.initialize.assert_called_once()

        # Verify download_folder_from_s3 was called with correct parameters
        mock_s3_tool.download_folder_from_s3.assert_called_once_with(
            input_params.bucket_name, input_params.folder_path
        )

        # Verify result
        assert result == mock_output
