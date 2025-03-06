import os
from dotenv import load_dotenv
from typing import Optional
from pathlib import Path

load_dotenv(override=True)

DEVELOPMENT = "development"
PRODUCTION = "production"
LOCAL = "local"


class Settings:
    GCP_PROJECT_ID: str = os.environ.get("GCP_PROJECT_ID", "")
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", DEVELOPMENT)
    ENABLE_JSON_LOGGING: bool = ENVIRONMENT != LOCAL
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
    LANGFUSE_HOST: str = os.environ.get("LANGFUSE_HOST", "")
    LANGFUSE_PUBLIC_KEY: str = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.environ.get("LANGFUSE_SECRET_KEY", "")
    GMAIL_TOKEN: str = os.environ.get("GMAIL_TOKEN", "")
    POSTGRES_HOST: str = os.environ.get("POSTGRES_HOST", "")
    POSTGRES_PORT: str = os.environ.get("POSTGRES_PORT", "")
    POSTGRES_DATABASE: str = os.environ.get("POSTGRES_DATABASE", "")
    POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "")
    AP_AGENT_EMAILS_BUCKET: str = os.environ.get("AP_AGENT_EMAILS_BUCKET", "")
    TEMPORAL_HOST: str = os.environ.get("TEMPORAL_HOST", "")
    TEMPORAL_NAMESPACE: str = os.environ.get("TEMPORAL_NAMESPACE", "")
    WINDMILL_SEND_SLACK_MESSAGE_API_TOKEN: str = os.environ.get(
        "WINDMILL_SEND_SLACK_MESSAGE_API_TOKEN", ""
    )
    WINDMILL_SEND_SLACK_MESSAGE_API_URL: str = os.environ.get(
        "WINDMILL_SEND_SLACK_MESSAGE_API_URL", ""
    )
    MERCURY_API_KEY: str = os.environ.get("MERCURY_API_KEY", "")
    SNOWFLAKE_USER: str = os.environ.get("SNOWFLAKE_USER", "")
    SNOWFLAKE_PASSWORD: str = os.environ.get("SNOWFLAKE_PASSWORD", "")
    SNOWFLAKE_ACCOUNT: str = os.environ.get("SNOWFLAKE_ACCOUNT", "")
    SNOWFLAKE_WAREHOUSE: str = os.environ.get("SNOWFLAKE_WAREHOUSE", "")
    SNOWFLAKE_DATABASE: str = os.environ.get("SNOWFLAKE_DATABASE", "")
    SNOWFLAKE_SCHEMA: str = os.environ.get("SNOWFLAKE_SCHEMA", "")
    TEMPORAL_LARGE_PAYLOAD_BUCKET: str = os.environ.get(
        "TEMPORAL_LARGE_PAYLOAD_BUCKET", ""
    )

    AWS_ACCESS_KEY_ID: str = os.environ.get("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.environ.get("AWS_REGION", "")
    PANTHEON_S3_BUCKET: str = os.environ.get("PANTHEON_S3_BUCKET", "")

    @staticmethod
    def is_cloud() -> bool:
        """
        Determine if Temporal should use cloud configuration based on environment.

        Returns:
            bool: True if should use cloud configuration, False for local
        """
        if Settings.ENVIRONMENT == LOCAL:
            return False
        else:
            return True

    @staticmethod
    def read_cert_file(file_path: Path) -> Optional[str]:
        """
        Read certificate file content.

        Args:
            file_path: Path to the certificate file

        Returns:
            str: Content of the certificate file if exists, None otherwise
        """
        try:
            if file_path.exists():
                return file_path.read_text()
            return None
        except Exception as e:
            print(f"Error reading certificate file {file_path}: {str(e)}")
            return None

    @staticmethod
    def get_temporal_certs() -> tuple[Optional[str], Optional[str]]:
        """
        Get all Temporal certificates content from root directory.

        Returns:
            tuple: (client_cert, client_key)
        """
        ROOT_DIR = Path(__file__).parent.parent.parent  # Goes up to the project root
        TEMPORAL_CLIENT_CERT_PATH: Path = ROOT_DIR / ".temporal-cert"
        TEMPORAL_CLIENT_KEY_PATH: Path = ROOT_DIR / ".temporal-key"
        client_cert = Settings.read_cert_file(TEMPORAL_CLIENT_CERT_PATH)
        client_key = Settings.read_cert_file(TEMPORAL_CLIENT_KEY_PATH)

        return client_cert, client_key
