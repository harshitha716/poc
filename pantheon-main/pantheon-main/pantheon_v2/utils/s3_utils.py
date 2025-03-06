from urllib.parse import urlparse
from typing import Tuple


def validate_s3_url(url: str, field_name: str = "url") -> None:
    """Validate if a given URL is a valid S3 URI"""
    if not url:
        raise ValueError(f"{field_name} is required")

    parsed = urlparse(url)
    if parsed.scheme != "s3":
        raise ValueError(f"{field_name} must be an S3 URI (starting with s3://)")

    if not parsed.netloc:
        raise ValueError(f"Invalid S3 URI: missing bucket name in {field_name}")

    if not parsed.path or parsed.path == "/":
        raise ValueError(f"Invalid S3 URI: missing file path in {field_name}")


def extract_s3_info(url: str) -> Tuple[str, str]:
    """Extract bucket name and file path from S3 URL"""
    parsed = urlparse(url)
    return parsed.netloc, parsed.path.lstrip("/")
