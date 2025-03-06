from io import BytesIO
from typing import Dict
from datetime import datetime
from pydantic import BaseModel, Field
from pantheon_v2.core.custom_data_types.pydantic import SerializableBytesIO


class DownloadFromS3Input(BaseModel):
    bucket_name: str = Field(..., description="Name of the S3 bucket to download from")
    file_name: str = Field(..., description="Name of the file to download")


class DownloadFromS3Output(BaseModel):
    content: SerializableBytesIO = Field(
        ..., description="File content as BytesIO object"
    )

    class Config:
        arbitrary_types_allowed = True


class DownloadFromS3OutputTemporal(BaseModel):
    content: str = Field(..., description="File content as BytesIO object")


class UploadToS3Input(BaseModel):
    bucket_name: str = Field(..., description="Name of the S3 bucket to upload to")
    file_name: str = Field(..., description="Name to give the uploaded file")
    blob: SerializableBytesIO = Field(..., description="File content as BytesIO object")
    content_type: str = Field(
        default="application/octet-stream", description="Content type of the file"
    )

    class Config:
        arbitrary_types_allowed = True


class UploadToS3Output(BaseModel):
    metadata: Dict = Field(..., description="Metadata of the uploaded file")
    s3_url: str = Field(..., description="S3 URL of the uploaded file (s3://...)")
    https_url: str = Field(
        ...,
        description="HTTPS URL of the uploaded file (https://s3.amazonaws.com/...)",
    )


class S3FileMetadata(BaseModel):
    name: str = Field(..., description="Name of the file")
    full_path: str = Field(..., description="Full path of the file in S3")
    relative_path: str = Field(
        ..., description="Path relative to the folder being downloaded"
    )
    size: int = Field(..., description="Size of the file in bytes")
    content_type: str = Field(..., description="Content type of the file")
    last_modified: datetime = Field(..., description="Last modification timestamp")
    content: BytesIO = Field(..., description="File content as BytesIO object")

    class Config:
        arbitrary_types_allowed = True


class DownloadFolderFromS3Output(BaseModel):
    message: str = Field(..., description="Status message")
    files: list[S3FileMetadata] = Field(
        ..., description="List of downloaded files with metadata"
    )

    class Config:
        arbitrary_types_allowed = True


class DownloadFolderFromS3Input(BaseModel):
    bucket_name: str = Field(..., description="Name of the S3 bucket to download from")
    folder_path: str = Field(..., description="Path to the folder to download")
