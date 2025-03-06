from pydantic import BaseModel, Field


class EmailParserConfig(BaseModel):
    default_encoding: str = Field(
        default="utf-8", description="Default encoding to use when parsing emails"
    )
    max_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum size of email content to process in bytes",
    )
