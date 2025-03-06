from pantheon_v2.tools.external.postgres.config import PostgresConfig
from pantheon_v2.tools.external.gcs.config import GCSConfig
from pantheon_v2.settings.settings import Settings

INTERNAL_POSTGRES_CONFIG = PostgresConfig(
    host=Settings.POSTGRES_HOST,
    port=Settings.POSTGRES_PORT,
    database=Settings.POSTGRES_DATABASE,
    username=Settings.POSTGRES_USER,
    password=Settings.POSTGRES_PASSWORD,
)

INTERNAL_GCS_CONFIG = GCSConfig(
    project_id=Settings.GCP_PROJECT_ID,
)
