import pytest
from pantheon_v2.utils.s3_utils import validate_s3_url, extract_s3_info


class TestS3Utils:
    def test_validate_s3_url_valid(self):
        """Test validation of valid S3 URLs"""
        # These should not raise any exceptions
        validate_s3_url("s3://my-bucket/path/to/file.txt")
        validate_s3_url("s3://my-bucket/file.txt")
        validate_s3_url("s3://my-bucket/path/to/nested/file.txt")

    def test_validate_s3_url_empty(self):
        """Test validation with empty URL"""
        with pytest.raises(ValueError) as exc_info:
            validate_s3_url("")
        assert str(exc_info.value) == "url is required"

        with pytest.raises(ValueError) as exc_info:
            validate_s3_url("", field_name="input_url")
        assert str(exc_info.value) == "input_url is required"

    def test_validate_s3_url_invalid_scheme(self):
        """Test validation with invalid URL scheme"""
        invalid_urls = [
            "http://my-bucket/file.txt",
            "https://my-bucket/file.txt",
            "ftp://my-bucket/file.txt",
            "my-bucket/file.txt",
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError) as exc_info:
                validate_s3_url(url)
            assert str(exc_info.value) == "url must be an S3 URI (starting with s3://)"

            with pytest.raises(ValueError) as exc_info:
                validate_s3_url(url, field_name="input_url")
            assert (
                str(exc_info.value)
                == "input_url must be an S3 URI (starting with s3://)"
            )

    def test_validate_s3_url_missing_bucket(self):
        """Test validation with missing bucket name"""
        invalid_urls = [
            "s3:///path/to/file.txt",
            "s3://",
            "s3:///",
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError) as exc_info:
                validate_s3_url(url)
            assert str(exc_info.value) == "Invalid S3 URI: missing bucket name in url"

    def test_validate_s3_url_missing_path(self):
        """Test validation with missing file path"""
        invalid_urls = [
            "s3://my-bucket",
            "s3://my-bucket/",
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError) as exc_info:
                validate_s3_url(url)
            assert str(exc_info.value) == "Invalid S3 URI: missing file path in url"

    def test_extract_s3_info_valid(self):
        """Test extracting information from valid S3 URLs"""
        test_cases = [
            {
                "url": "s3://my-bucket/path/to/file.txt",
                "expected": ("my-bucket", "path/to/file.txt"),
            },
            {"url": "s3://my-bucket/file.txt", "expected": ("my-bucket", "file.txt")},
            {
                "url": "s3://my-bucket/deeply/nested/path/file.txt",
                "expected": ("my-bucket", "deeply/nested/path/file.txt"),
            },
            {
                "url": "s3://my-bucket-with-dashes/file.txt",
                "expected": ("my-bucket-with-dashes", "file.txt"),
            },
            {
                "url": "s3://my.bucket.with.dots/file.txt",
                "expected": ("my.bucket.with.dots", "file.txt"),
            },
        ]

        for test_case in test_cases:
            bucket, path = extract_s3_info(test_case["url"])
            assert (bucket, path) == test_case["expected"]

    def test_extract_s3_info_with_leading_slash(self):
        """Test extracting information from S3 URLs with leading slashes"""
        bucket, path = extract_s3_info("s3://my-bucket//path/to/file.txt")
        assert bucket == "my-bucket"
        assert path == "path/to/file.txt"

        bucket, path = extract_s3_info("s3://my-bucket///deeply/nested/file.txt")
        assert bucket == "my-bucket"
        assert path == "deeply/nested/file.txt"
