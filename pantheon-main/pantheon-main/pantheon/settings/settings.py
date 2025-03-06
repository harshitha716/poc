import os
from dotenv import load_dotenv

load_dotenv()

DEVELOPMENT = "development"
PRODUCTION = "production"
LOCAL = "local"


class Settings:
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", DEVELOPMENT)
    ENABLE_JSON_LOGGING: bool = ENVIRONMENT != LOCAL
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
    HERM_PROXY_URL: str = os.environ.get("HERM_PROXY_URL", "")
