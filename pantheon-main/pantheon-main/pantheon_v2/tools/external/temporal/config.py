from pydantic import BaseModel, Field


class TemporalConfig(BaseModel):
    host: str = Field(..., description="Temporal server host")
    namespace: str = Field(default="default", description="Temporal namespace")
    is_cloud: bool = Field(default=False, description="Whether using Temporal Cloud")
    client_cert: str | None = Field(
        default=None, description="Client certificate for TLS"
    )
    client_key: str | None = Field(default=None, description="Client key for TLS")
    server_root_ca_cert: str | None = Field(
        default=None, description="Server root CA cert"
    )
