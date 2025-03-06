from pydantic import BaseModel, Field


class S3Config(BaseModel):
    aws_access_key: str = Field(..., description="AWS Access Key")
    aws_secret_key: str = Field(..., description="AWS Secret Key")
    region_name: str = Field(default="us-east-1", description="AWS Region")
