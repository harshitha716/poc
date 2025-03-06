from pydantic import BaseModel, Field


class GCSConfig(BaseModel):
    project_id: str = Field(..., description="The GCP project ID")
