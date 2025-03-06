import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from datetime import datetime

from pantheon_v2.tools.external.s3.tool import S3Tool
from pantheon_v2.tools.external.s3.models import (
    DownloadFromS3Input,
    UploadToS3Input,
)


@pytest.fixture
def s3_config():
    return {
        "aws_access_key": "test_key",
        "aws_secret_key": "test_secret",
        "region_name": "us-east-1",
    }


@pytest.fixture
def s3_tool(s3_config):
    tool = S3Tool(config=s3_config)
    tool.s3_client = MagicMock()
    return tool


class TestS3Tool:
    @pytest.mark.asyncio
    async def test_initialize_success(self, s3_config):
        """Test successful initialization of S3Tool"""
        with patch("pantheon_v2.tools.external.s3.tool.boto3.client") as mock_client:
            mock_client.return_value = MagicMock()
            tool = S3Tool(config=s3_config)
            await tool.initialize()
            mock_client.assert_called_once_with(
                "s3",
                aws_access_key_id=s3_config["aws_access_key"],
                aws_secret_access_key=s3_config["aws_secret_key"],
                region_name=s3_config["region_name"],
            )
            assert tool.s3_client is not None

    @pytest.mark.asyncio
    async def test_initialize_failure(self, s3_config):
        """Test initialization failure of S3Tool"""
        with patch(
            "pantheon_v2.tools.external.s3.tool.boto3.client",
            side_effect=Exception("AWS Error"),
        ):
            tool = S3Tool(config=s3_config)
            with pytest.raises(Exception) as exc_info:
                await tool.initialize()
            assert str(exc_info.value) == "AWS Error"

    @pytest.mark.asyncio
    async def test_download_from_s3(self, s3_tool):
        # Arrange
        test_content = b"test content"
        mock_body = MagicMock()
        mock_body.read.return_value = test_content

        s3_tool.s3_client.get_object.return_value = {"Body": mock_body}

        input_data = DownloadFromS3Input(
            bucket_name="test-bucket", file_name="test.pdf"
        )

        # Act
        result = await s3_tool.download_from_s3(input_data)

        # Assert
        s3_tool.s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="test.pdf"
        )
        assert result.content.getvalue() == test_content

    @pytest.mark.asyncio
    async def test_upload_to_s3(self, s3_tool):
        # Arrange
        test_content = BytesIO(b"test content")
        input_data = UploadToS3Input(
            bucket_name="test-bucket",
            file_name="test.pdf",
            blob=test_content,
            content_type="application/octet-stream",
        )

        mock_head_response = {
            "ContentLength": 1234,
            "ContentType": "application/pdf",
            "ETag": "test_etag",
            "LastModified": datetime(2024, 1, 1),
        }
        s3_tool.s3_client.head_object.return_value = mock_head_response

        # Act
        result = await s3_tool.upload_to_s3(input_data)

        # Assert
        s3_tool.s3_client.upload_fileobj.assert_called_once_with(
            test_content,
            "test-bucket",
            "test.pdf",
            ExtraArgs={"ContentType": "application/pdf"},
        )

        s3_tool.s3_client.head_object.assert_called_once_with(
            Bucket="test-bucket", Key="test.pdf"
        )

        assert result.s3_url == "s3://test-bucket/test.pdf"
        assert result.https_url == "https://s3.amazonaws.com/test-bucket/test.pdf"
        assert result.metadata == {
            "bucket": "test-bucket",
            "name": "test.pdf",
            "size": 1234,
            "content_type": "application/pdf",
            "etag": "test_etag",
            "last_modified": "2024-01-01 00:00:00",
        }

    @pytest.mark.asyncio
    async def test_download_folder_from_s3(self, s3_tool):
        # Arrange
        mock_objects = {
            "Contents": [
                {
                    "Key": "test_folder/test1.pdf",
                    "Size": 1234,
                    "LastModified": datetime(2024, 1, 1),
                },
                {
                    "Key": "test_folder/",
                    "Size": 0,
                    "LastModified": datetime(2024, 1, 1),
                },
                {
                    "Key": "test_folder/test2.txt",
                    "Size": 5678,
                    "LastModified": datetime(2024, 1, 2),
                },
            ]
        }

        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [mock_objects]
        s3_tool.s3_client.get_paginator.return_value = mock_paginator

        def mock_get_object(Bucket, Key):
            return {
                "Body": MagicMock(read=lambda: b"test content"),
                "ContentType": "application/pdf"
                if Key.endswith(".pdf")
                else "text/plain",
            }

        s3_tool.s3_client.get_object.side_effect = mock_get_object

        # Act
        result = await s3_tool.download_folder_from_s3("test-bucket", "test_folder")

        # Assert
        s3_tool.s3_client.get_paginator.assert_called_once_with("list_objects_v2")
        mock_paginator.paginate.assert_called_once_with(
            Bucket="test-bucket", Prefix="test_folder"
        )

        assert (
            len(result.files) == 2
        )  # Should only include actual files, not the folder
        assert result.message == "Downloaded 2 files"

        # Verify first file
        file1 = next(f for f in result.files if f.name == "test1.pdf")
        assert file1.full_path == "test_folder/test1.pdf"
        assert file1.relative_path == "test1.pdf"
        assert file1.size == 1234
        assert file1.content_type == "application/pdf"
        assert file1.last_modified == datetime(2024, 1, 1)
        assert file1.content.getvalue() == b"test content"

        # Verify second file
        file2 = next(f for f in result.files if f.name == "test2.txt")
        assert file2.full_path == "test_folder/test2.txt"
        assert file2.relative_path == "test2.txt"
        assert file2.size == 5678
        assert file2.content_type == "text/plain"
        assert file2.last_modified == datetime(2024, 1, 2)
        assert file2.content.getvalue() == b"test content"
