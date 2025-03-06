from pantheon.settings.settings import Settings
from pantheon.settings.logging import configure_logger as configure_logger

settings = Settings()
configure_logger(enable_json_logs=settings.ENABLE_JSON_LOGGING)
