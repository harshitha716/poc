import structlog
import os
import boto3
from io import BytesIO
import mimetypes

from pantheon_v2.tools.external.s3.models import (
    DownloadFromS3Input,
    DownloadFromS3Output,
    UploadToS3Input,
    UploadToS3Output,
    DownloadFolderFromS3Output,
    S3FileMetadata,
)
from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.core.tool_registry import ToolRegistry
from pantheon_v2.tools.external.s3.config import S3Config
from pantheon_v2.tools.external.s3.constants import S3_HTTPS_BASE_URL

logger = structlog.get_logger(__name__)


@ToolRegistry.register_tool(description="Amazon S3 tool for file operations")
class S3Tool(BaseTool):
    def __init__(self, config: dict):
        self.s3_client = None
        self.config = config

    async def initialize(self) -> None:
        """Initialize the S3 client asynchronously"""
        try:
            config = S3Config(**self.config)

            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=config.aws_access_key,
                aws_secret_access_key=config.aws_secret_key,
                region_name=config.region_name,
            )
            logger.info("S3 tool initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize S3 tool", error=str(e))
            raise

    @ToolRegistry.register_tool_action(description="Download a file from Amazon S3")
    async def download_from_s3(
        self, params: DownloadFromS3Input
    ) -> DownloadFromS3Output:
        response = self.s3_client.get_object(
            Bucket=params.bucket_name, Key=params.file_name
        )

        # Create an in-memory file-like object
        bytes_buffer = BytesIO(response["Body"].read())
        bytes_buffer.seek(0)  # Move to the beginning of the file-like object

        return DownloadFromS3Output(content=bytes_buffer)

    @ToolRegistry.register_tool_action(description="Upload a file to Amazon S3")
    async def upload_to_s3(self, params: UploadToS3Input) -> UploadToS3Output:
        # Detect content type from the file name if not provided
        content_type = params.content_type
        if content_type == "application/octet-stream":
            guessed_type, _ = mimetypes.guess_type(params.file_name)
            if guessed_type is not None:
                content_type = guessed_type

        # Use the existing BytesIO object directly
        params.blob.seek(0)  # Ensure we're at the start of the BytesIO object

        # Upload the file
        self.s3_client.upload_fileobj(
            params.blob,
            params.bucket_name,
            params.file_name,
            ExtraArgs={"ContentType": content_type},
        )

        # Get object metadata
        response = self.s3_client.head_object(
            Bucket=params.bucket_name, Key=params.file_name
        )

        # Convert last_modified to string if it exists
        last_modified = response.get("LastModified", "")
        if last_modified:
            last_modified = last_modified.strftime("%Y-%m-%d %H:%M:%S")

        metadata = {
            "bucket": params.bucket_name,
            "name": params.file_name,
            "size": response.get("ContentLength", 0),
            "content_type": response.get("ContentType", content_type),
            "etag": response.get("ETag", ""),
            "last_modified": last_modified,
        }

        s3_url = f"s3://{params.bucket_name}/{params.file_name}"
        https_url = f"{S3_HTTPS_BASE_URL}/{params.bucket_name}/{params.file_name}"

        return UploadToS3Output(metadata=metadata, s3_url=s3_url, https_url=https_url)

    @ToolRegistry.register_tool_action(description="Download a folder from Amazon S3")
    async def download_folder_from_s3(
        self,
        bucket_name: str,
        folder_path: str,
    ) -> DownloadFolderFromS3Output:
        """Downloads all contents of an S3 folder and returns array of BytesIO objects with metadata"""
        # List objects in the folder
        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name, Prefix=folder_path)

        downloaded_files = []
        for page in pages:
            for obj in page.get("Contents", []):
                if obj["Key"].endswith("/"):  # Skip folder markers
                    continue

                # Download the file
                response = self.s3_client.get_object(Bucket=bucket_name, Key=obj["Key"])

                # Create BytesIO object for the file
                bytes_buffer = BytesIO(response["Body"].read())
                bytes_buffer.seek(0)

                # Extract relative path by removing the folder_path prefix
                relative_path = obj["Key"].replace(folder_path, "").lstrip("/")

                # Create metadata object
                metadata = S3FileMetadata(
                    name=os.path.basename(obj["Key"]),
                    full_path=obj["Key"],
                    relative_path=relative_path,
                    size=obj["Size"],
                    content_type=response.get(
                        "ContentType", "application/octet-stream"
                    ),
                    last_modified=obj["LastModified"],
                    content=bytes_buffer,
                )

                downloaded_files.append(metadata)

        return DownloadFolderFromS3Output(
            message=f"Downloaded {len(downloaded_files)} files", files=downloaded_files
        )
