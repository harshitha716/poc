import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from datetime import datetime

from pantheon_v2.tools.external.gcs.tool import GCSTool
from pantheon_v2.tools.external.gcs.models import (
    UploadToGCSInput,
    DownloadFromGCSInput,
)


@pytest.fixture
def gcs_config():
    return {
        "project_id": "test-project",
    }


@pytest.fixture
def mock_gcs_blob():
    mock_blob = MagicMock()
    mock_blob.size = 1234
    mock_blob.content_type = "application/pdf"
    mock_blob.etag = "test_etag"
    mock_blob.generation = "test_generation"
    mock_blob.metageneration = "test_metageneration"
    mock_blob.time_created = datetime(2024, 1, 1)
    mock_blob.updated = datetime(2024, 1, 2)
    return mock_blob


@pytest.fixture
def gcs_tool(gcs_config):
    tool = GCSTool(config=gcs_config)
    tool.storage_client = MagicMock()
    return tool


class TestGCSTool:
    @pytest.mark.asyncio
    async def test_initialize_success(self, gcs_tool):
        """Test successful initialization of GCSTool"""
        with patch("pantheon_v2.tools.external.gcs.tool.storage.Client") as mock_client:
            mock_client.return_value = MagicMock()
            await gcs_tool.initialize()
            mock_client.assert_called_once_with("test-project")
            assert gcs_tool.storage_client is not None

    @pytest.mark.asyncio
    async def test_initialize_failure(self, gcs_tool):
        """Test initialization failure of GCSTool"""
        with patch(
            "pantheon_v2.tools.external.gcs.tool.storage.Client",
            side_effect=Exception("GCS Error"),
        ):
            with pytest.raises(Exception) as exc_info:
                await gcs_tool.initialize()
            assert str(exc_info.value) == "GCS Error"

    @pytest.mark.asyncio
    async def test_upload_to_gcs(self, gcs_tool, mock_gcs_blob):
        # Arrange
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_gcs_blob
        gcs_tool.storage_client.get_bucket.return_value = mock_bucket

        # Set content_disposition to None to match expected metadata
        mock_gcs_blob.content_disposition = None

        test_content = BytesIO(b"test content")
        input_data = UploadToGCSInput(
            bucket_name="test-bucket", file_name="test.pdf", blob=test_content
        )

        # Act
        result = await gcs_tool.upload_to_gcs(input_data)

        # Assert
        gcs_tool.storage_client.get_bucket.assert_called_once_with("test-bucket")
        mock_bucket.blob.assert_called_once_with("test.pdf")
        mock_gcs_blob.upload_from_file.assert_called_once_with(
            test_content, content_type="application/pdf"
        )

        assert result.gcs_url == "gs://test-bucket/test.pdf"
        assert result.https_url == "https://storage.googleapis.com/test-bucket/test.pdf"
        assert result.metadata == {
            "bucket": "test-bucket",
            "name": "test.pdf",
            "size": 1234,
            "content_type": "application/pdf",
            "etag": "test_etag",
            "generation": "test_generation",
            "metageneration": "test_metageneration",
            "content_disposition": None,  # Include this in expected metadata
        }

    @pytest.mark.asyncio
    async def test_download_from_gcs(self, gcs_tool, mock_gcs_blob):
        # Arrange
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_gcs_blob
        gcs_tool.storage_client.get_bucket.return_value = mock_bucket

        def mock_download(buffer):
            buffer.write(b"test content")

        mock_gcs_blob.download_to_file.side_effect = mock_download

        input_data = DownloadFromGCSInput(
            bucket_name="test-bucket", file_name="test.pdf"
        )

        # Act
        result = await gcs_tool.download_from_gcs(input_data)

        # Assert
        gcs_tool.storage_client.get_bucket.assert_called_once_with("test-bucket")
        mock_bucket.blob.assert_called_once_with("test.pdf")
        mock_gcs_blob.download_to_file.assert_called_once()
        assert result.content.getvalue() == b"test content"

    @pytest.mark.asyncio
    async def test_download_folder_from_gcs(self, gcs_tool, mock_gcs_blob):
        # Arrange
        mock_bucket = MagicMock()
        gcs_tool.storage_client.get_bucket.return_value = mock_bucket

        # Create two mock blobs - one file and one folder
        mock_file_blob = mock_gcs_blob
        mock_file_blob.name = "test_folder/test.pdf"

        mock_folder_blob = MagicMock()
        mock_folder_blob.name = "test_folder/"

        mock_bucket.list_blobs.return_value = [mock_file_blob, mock_folder_blob]

        def mock_download(buffer):
            buffer.write(b"test content")

        mock_file_blob.download_to_file.side_effect = mock_download

        # Act
        result = await gcs_tool.download_folder_from_gcs("test-bucket", "test_folder")

        # Assert
        gcs_tool.storage_client.get_bucket.assert_called_once_with("test-bucket")
        mock_bucket.list_blobs.assert_called_once_with(prefix="test_folder")

        assert len(result.files) == 1  # Should only include the file, not the folder
        file_metadata = result.files[0]
        assert file_metadata.name == "test.pdf"
        assert file_metadata.full_path == "gs://test-bucket/test_folder/test.pdf"
        assert file_metadata.relative_path == "test.pdf"
        assert file_metadata.size == 1234
        assert file_metadata.content_type == "application/pdf"
        assert file_metadata.created == datetime(2024, 1, 1)
        assert file_metadata.updated == datetime(2024, 1, 2)
        assert file_metadata.content.getvalue() == b"test content"
        assert result.message == "Downloaded 1 files"


# pytest --cov=pantheon_v2/tools/ocr --cov-report=term-missing pantheon_v2/tools/ocr/tests/ -v
