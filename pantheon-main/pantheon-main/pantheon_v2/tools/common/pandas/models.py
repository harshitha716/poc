from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from pantheon_v2.core.custom_data_types.pydantic import SerializableBytesIO
import pandas as pd
from io import BytesIO


class ConvertFileToDFOutput(BaseModel):
    success: bool = Field(..., description="Whether the execution was successful")
    result: Optional[str] = Field(
        None,
        description="Result of the function execution if successful, as JSON string in split orientation",
    )

    @classmethod
    def from_dataframe(
        cls, df: Optional[pd.DataFrame], success: bool = True
    ) -> "ConvertFileToDFOutput":
        if df is None or not success:
            return cls(success=success, result=None)
        return cls(success=success, result=df.to_json(orient="split"))

    def to_dataframe(self) -> Optional[pd.DataFrame]:
        if not self.success or self.result is None:
            return None
        return pd.read_json(self.result, orient="split")


class DataFrameInfo(BaseModel):
    df: pd.DataFrame = Field(..., description="DataFrame to get info from")

    class Config:
        arbitrary_types_allowed = True


class FileToPandasInput(BaseModel):
    file_content: SerializableBytesIO = Field(
        ..., description="File content as BytesIO object"
    )
    file_name: str = Field(..., description="File name")

    class Config:
        arbitrary_types_allowed = True


class FileBytes(BaseModel):
    file_bytes: BytesIO

    class Config:
        arbitrary_types_allowed = True


class DataFrameModel(BaseModel):
    df: pd.DataFrame

    class Config:
        arbitrary_types_allowed = True


class DetectTablesAndMetadataInput(BaseModel):
    file_content: str = Field(..., description="File content as string")


class DetectTablesAndMetadataOutput(BaseModel):
    table_df: Optional[str] = Field(
        None, description="Table DataFrame as JSON string in split orientation"
    )
    metadata_df: Optional[str] = Field(
        None, description="Metadata DataFrame as JSON string in split orientation"
    )
    success: bool = Field(..., description="Whether the execution was successful")

    @classmethod
    def from_dataframe(
        cls,
        table_df: Optional[pd.DataFrame],
        metadata_df: Optional[pd.DataFrame],
        success: bool,
    ) -> "DetectTablesAndMetadataOutput":
        if table_df is None or metadata_df is None or not success:
            return cls(table_df=None, metadata_df=None, success=False)
        return cls(
            table_df=table_df.to_json(orient="split"),
            metadata_df=metadata_df.to_json(orient="split"),
            success=success,
        )

    def to_dataframes(self) -> tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        if not self.success or self.table_df is None or self.metadata_df is None:
            return None, None
        return (
            pd.read_json(self.table_df, orient="split"),
            pd.read_json(self.metadata_df, orient="split"),
        )


class AddMetadataColumnsInput(BaseModel):
    file_content: str = Field(
        ..., description="DataFrame content as JSON string in split orientation"
    )
    metadata: Dict[str, Any] = Field(
        ...,
        description="Metadata dictionary containing key-value pairs to add as columns",
    )


class AddMetadataColumnsOutput(BaseModel):
    result_df: Optional[str] = Field(
        None, description="Result DataFrame as JSON string in split orientation"
    )
    success: bool = Field(..., description="Whether the execution was successful")

    @classmethod
    def from_dataframe(
        cls, df: Optional[pd.DataFrame], success: bool = True
    ) -> "AddMetadataColumnsOutput":
        if df is None or not success:
            return cls(result_df=None, success=False)
        return cls(result_df=df.to_json(orient="split"), success=success)

    def to_dataframe(self) -> Optional[pd.DataFrame]:
        if not self.success or self.result_df is None:
            return None
        return pd.read_json(self.result_df, orient="split")


class DFToCSVInput(BaseModel):
    file_content: str = Field(
        ..., description="DataFrame content as JSON string in split orientation"
    )


class DFToCSVOutput(BaseModel):
    csv_content: Optional[SerializableBytesIO] = Field(
        None, description="CSV content as SerializableBytesIO object"
    )
    success: bool = Field(..., description="Whether the execution was successful")

    class Config:
        arbitrary_types_allowed = True


class DFToParquetInput(BaseModel):
    file_content: str = Field(
        ..., description="DataFrame content as JSON string in split orientation"
    )


class DFToParquetOutput(BaseModel):
    parquet_content: Optional[SerializableBytesIO] = Field(
        None, description="Parquet content as SerializableBytesIO object"
    )
    success: bool = Field(..., description="Whether the execution was successful")

    class Config:
        arbitrary_types_allowed = True


class DataPreviewInput(BaseModel):
    """Input model for data preview generation"""

    df_json: str = Field(
        ..., description="DataFrame as JSON string in split orientation"
    )
    num_rows: int = Field(default=50, description="Number of rows to preview")


class DataPreviewOutput(BaseModel):
    """Output model for data preview"""

    columns: List[str] = Field(..., description="List of column names")
    rows: List[Dict[str, Any]] = Field(
        ..., description="List of rows with column name as key"
    )
