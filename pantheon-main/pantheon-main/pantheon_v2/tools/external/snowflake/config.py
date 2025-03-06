from pydantic import BaseModel, Field


class SnowflakeConfig(BaseModel):
    user: str = Field(..., description="Snowflake user")
    password: str = Field(..., description="Snowflake password")
    account: str = Field(..., description="Snowflake account")
    warehouse: str = Field(..., description="Snowflake warehouse")
    database: str = Field(..., description="Snowflake database")
    schema: str = Field(..., description="Snowflake schema")
