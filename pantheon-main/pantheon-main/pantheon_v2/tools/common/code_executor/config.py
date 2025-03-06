from pydantic import BaseModel, Field


class CodeExecutorConfig(BaseModel):
    timeout_seconds: int = Field(
        default=30,
        description="Maximum execution time allowed for functions in seconds",
    )
