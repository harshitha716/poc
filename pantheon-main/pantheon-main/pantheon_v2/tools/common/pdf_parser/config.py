from pydantic import BaseModel, Field


class PDFParserConfig(BaseModel):
    max_size: int = Field(
        default=50 * 1024 * 1024,  # 50MB
        description="Maximum size of PDF content to process in bytes",
    )
    table_settings: dict = Field(
        default={
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            "snap_tolerance": 3,
            "join_tolerance": 3,
        },
        description="Settings for table extraction",
    )
