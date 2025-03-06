from pydantic import BaseModel, Field


class PostgresConfig(BaseModel):
    host: str = Field(..., description="Database host")
    port: str = Field("5432", description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    pool_size: int = Field(5, description="Connection pool size")
    max_overflow: int = Field(
        10,
        description="Maximum number of connections that can be created beyond pool_size",
    )
    pool_timeout: int = Field(
        30,
        description="Seconds to wait before giving up on getting a connection from the pool",
    )
    pool_recycle: int = Field(
        3600, description="Seconds after which a connection is automatically recycled"
    )
