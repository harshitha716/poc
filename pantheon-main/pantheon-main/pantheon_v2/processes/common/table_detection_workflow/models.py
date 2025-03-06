from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from pantheon_v2.processes.common.table_detection_workflow.business_logic.models import (
    ColumnMapping,
    MissingColumns,
)


class TableDetectionInput(BaseModel):
    """Input model for table detection workflow"""

    source_file_path: str = Field(..., description="Path of the input file in storage")
    source_bucket: str = Field(..., description="Bucket name containing the input file")
    output_format_path: Optional[str] = Field(
        None, description="Path of the output format file in storage"
    )
    output_format_bucket: Optional[str] = Field(
        None, description="Bucket name containing the output format file"
    )
    config: Optional[Dict[str, Any]] = Field(
        None, description="Additional configuration for file import"
    )


class ColumnMappingResult(BaseModel):
    """Model for column mapping results"""

    mapped_columns: List[ColumnMapping] = Field(
        default_factory=list,
        description="List of successful column mappings with confidence scores",
    )
    missing_columns: MissingColumns = Field(
        default_factory=MissingColumns,
        description="Columns that couldn't be mapped from both source and target",
    )
    document_type: str = Field(
        ..., description="Type of document inferred from the column patterns"
    )
    confidence: float = Field(
        ..., description="Overall confidence score for document type detection"
    )


class DataPreview(BaseModel):
    """Model for data preview"""

    columns: List[str] = Field(..., description="List of column names")
    rows: List[Dict[str, Any]] = Field(
        ..., description="List of rows with column name as key"
    )


class TableDetectionOutput(BaseModel):
    """Output model for table detection workflow"""

    transformed_data_bucket: str = Field(
        ..., description="S3 bucket containing the transformed data"
    )
    transformed_data_path: str = Field(
        ..., description="Path of the transformed data in the bucket"
    )
    column_mapping: Optional[ColumnMappingResult] = Field(
        None, description="Column mapping results if output format was provided"
    )
    extracted_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Metadata extracted by LLM from the document"
    )
    data_preview: DataPreview = Field(
        ..., description="Preview of first 50 rows of data"
    )
