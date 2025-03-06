from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pantheon_v2.processes.common.table_detection_workflow.business_logic.constants import (
    MetadataMode,
)


class ColumnMapping(BaseModel):
    """Model for individual column mapping between source and target"""

    source_column: str = Field(
        ..., description="Name of the column in the source table"
    )
    target_column: str = Field(
        ..., description="Name of the matching column in the target format"
    )
    confidence: float = Field(
        ...,
        description="Confidence score between 0 and 1 indicating how certain the mapping is",
        ge=0,
        le=1,
    )
    mapping_reason: str = Field(
        ...,
        description="Detailed explanation of why this mapping was chosen, including semantic relationships, data pattern matches, etc.",
    )


class MissingColumns(BaseModel):
    """Model for tracking columns that couldn't be confidently mapped in either direction"""

    source: Optional[List[str]] = Field(
        default_factory=list,
        description="List of columns from the source table that couldn't be confidently mapped to any target column",
    )
    target: Optional[List[str]] = Field(
        default_factory=list,
        description="List of columns from the target format that couldn't be matched with any source column",
    )


class ColumnMappingOutput(BaseModel):
    """Output model for column mapping results between source and target formats"""

    mapped_columns: Optional[List[ColumnMapping]] = Field(
        default_factory=list,
        description="List of successful column mappings with confidence scores and reasoning",
    )
    missing_columns: Optional[MissingColumns] = Field(
        default_factory=MissingColumns,
        description="Tracking of columns that couldn't be mapped from both source and target",
    )
    document_type: str = Field(
        ...,
        description="Type of document inferred from the column patterns and data (e.g., 'Invoice', 'Purchase Order', etc.)",
    )
    confidence: float = Field(
        ...,
        description="Overall confidence score between 0 and 1 for document type detection",
        ge=0,
        le=1,
    )
    normalized_df: Optional[str] = Field(
        default=None,
        description="Normalized DataFrame as JSON string in split orientation",
    )


class ColumnMappingInput(BaseModel):
    """Input model for column mapping LLM call"""

    source_df: str = Field(
        ..., description="Source DataFrame as JSON string in split orientation"
    )
    target_df: str = Field(
        ..., description="Target format DataFrame as JSON string in split orientation"
    )
    sample_rows: int = Field(
        default=3, description="Number of sample rows to include for context"
    )


class MetadataOutput(BaseModel):
    """Model for metadata extraction output"""

    data: Dict[str, Any]


class LLMCallInput(BaseModel):
    """Input model for LLM call function"""

    metadata_df: str
    mode: MetadataMode = Field(
        default=MetadataMode.ALL, description="Mode of metadata extraction"
    )
    target_attributes: Optional[List[str]] = Field(
        default=None,
        description="List of target attributes to search for in targeted mode",
    )


class LLMCallOutput(BaseModel):
    """Output model for LLM call function"""

    extracted_data: MetadataOutput
