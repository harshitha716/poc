import structlog
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from io import BytesIO

from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.core.tool_registry import ToolRegistry

# from pantheon_v2.tools.common.pandas.config import PandasConfig
from pantheon_v2.tools.common.pandas.models import (
    FileToPandasInput,
    ConvertFileToDFOutput,
    FileBytes,
    DetectTablesAndMetadataInput,
    DetectTablesAndMetadataOutput,
    AddMetadataColumnsInput,
    AddMetadataColumnsOutput,
    DFToCSVInput,
    DFToCSVOutput,
    DFToParquetInput,
    DFToParquetOutput,
    DataPreviewInput,
    DataPreviewOutput,
)
from pantheon_v2.tools.common.pandas.helper import (
    process_excel_file,
    flexible_csv_parser,
    process_parquet_file,
)
from pantheon_v2.tools.common.pandas.helpers.add_metadata_columns import (
    add_metadata_to_df,
)
from pantheon_v2.tools.common.pandas.helpers.island_detection import (
    detect_tables_and_metadata,
)

logger = structlog.get_logger(__name__)


@ToolRegistry.register_tool(description="Tool for executing Pandas functions")
class PandasTool(BaseTool):
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor()

    async def initialize(self) -> None:
        """Initialize the code executor tool"""
        logger.info("Code executor tool initialized successfully")

    @ToolRegistry.register_tool_action(
        description="Execute a Python function with given arguments"
    )
    async def convert_file_to_df(
        self, params: FileToPandasInput
    ) -> ConvertFileToDFOutput:
        file_name = params.file_name
        file_bytes_model = FileBytes(file_bytes=params.file_content)

        try:
            if file_name.endswith((".xlsx", ".xls")):
                df = process_excel_file(params.file_content, file_name[-4:])
            elif file_name.endswith(".csv"):
                # Use the flexible_csv_parser for CSV files
                df_model = flexible_csv_parser(file_bytes_model)
                df = df_model.df
            elif file_name.endswith(".parquet"):
                # Process parquet files
                df = process_parquet_file(params.file_content)
            else:
                return ConvertFileToDFOutput.from_dataframe(None, success=False)

            return ConvertFileToDFOutput.from_dataframe(df, success=True)
        except Exception as e:
            logger.error("Error converting file to DataFrame", error=str(e))
            return ConvertFileToDFOutput.from_dataframe(None, success=False)

    @ToolRegistry.register_tool_action(
        description="Detect tables and metadata in a CSV file"
    )
    async def detect_tables_and_metadata(
        self, params: DetectTablesAndMetadataInput
    ) -> DetectTablesAndMetadataOutput:
        try:
            # The input is a DataFrame in split JSON format, so we should read it that way
            df = pd.read_json(params.file_content, orient="split")
            # Detect tables and metadata in the DataFrame
            result_df, metadata_df = detect_tables_and_metadata(df)
            result_df.reset_index(drop=True, inplace=True)

            return DetectTablesAndMetadataOutput(
                table_df=result_df.to_json(orient="split"),
                metadata_df=metadata_df.to_json(orient="split")
                if metadata_df is not None
                else None,
                success=True,
            )

        except Exception as e:
            logger.error("Error processing DataFrame for table detection", error=str(e))
            return DetectTablesAndMetadataOutput(
                table_df=None, metadata_df=None, success=False
            )

    @ToolRegistry.register_tool_action(
        description="Add metadata columns to a DataFrame"
    )
    async def add_columns_to_df(
        self, params: AddMetadataColumnsInput
    ) -> AddMetadataColumnsOutput:
        try:
            # Convert input JSON string to DataFrame and immediately drop index
            df = pd.read_json(params.file_content, orient="split")

            # Add metadata columns to the DataFrame
            result_df = add_metadata_to_df(df, params.metadata["data"])

            return AddMetadataColumnsOutput(
                result_df=result_df.to_json(orient="split"), success=True
            )

        except Exception as e:
            logger.error("Error adding metadata columns to DataFrame", error=str(e))
            return AddMetadataColumnsOutput(result_df=None, success=False)

    @ToolRegistry.register_tool_action(description="Convert DataFrame to CSV format")
    async def df_to_csv(self, params: DFToCSVInput) -> DFToCSVOutput:
        try:
            # Convert input JSON string to DataFrame
            df = pd.read_json(params.file_content, orient="split")

            # Check if headers are numeric to determine header inclusion
            headers = list(df.columns)
            are_headers_numeric = all(
                isinstance(h, (int, float)) or (isinstance(h, str) and h.isdigit())
                for h in headers
            )
            include_headers = (
                not are_headers_numeric
            )  # Include headers only if they're not numeric

            # Convert all columns to string type
            df = df.astype(str)

            # Convert to CSV bytes
            csv_buffer = BytesIO()
            df.to_csv(csv_buffer, index=False, header=include_headers, encoding="utf-8")
            csv_buffer.seek(0)

            logger.info(
                "Successfully converted DataFrame to CSV",
                num_rows=len(df),
                num_columns=len(df.columns),
                include_headers=include_headers,
            )

            return DFToCSVOutput(csv_content=csv_buffer, success=True)

        except Exception as e:
            logger.error("Error converting DataFrame to CSV", error=str(e))
            return DFToCSVOutput(csv_content=None, success=False)

    @ToolRegistry.register_tool_action(
        description="Convert DataFrame to Parquet format"
    )
    async def df_to_parquet(self, params: DFToParquetInput) -> DFToParquetOutput:
        try:
            # Convert input JSON string to DataFrame
            df = pd.read_json(params.file_content, orient="split")

            # Convert to Parquet bytes
            parquet_buffer = BytesIO()
            df.to_parquet(parquet_buffer, index=False)
            parquet_buffer.seek(0)

            logger.info(
                "Successfully converted DataFrame to Parquet",
                num_rows=len(df),
                num_columns=len(df.columns),
            )

            return DFToParquetOutput(parquet_content=parquet_buffer, success=True)

        except Exception as e:
            logger.error("Error converting DataFrame to Parquet", error=str(e))
            return DFToParquetOutput(parquet_content=None, success=False)

    @ToolRegistry.register_tool_action(
        description="Generate data preview from DataFrame JSON"
    )
    async def generate_data_preview(
        self, params: DataPreviewInput
    ) -> DataPreviewOutput:
        try:
            df = pd.read_json(params.df_json, orient="split")

            # Check if headers are numeric to determine header inclusion
            headers = list(df.columns)
            are_headers_numeric = all(
                isinstance(h, (int, float)) or (isinstance(h, str) and h.isdigit())
                for h in headers
            )

            # If headers are numeric, use first row as headers
            if are_headers_numeric:
                # Get the first row values
                new_headers = df.iloc[0].values.tolist()
                # Update column names
                df.columns = new_headers
                # Remove the first row since it's now headers
                df = df.iloc[1:]
                # Reset index after removing first row
                df = df.reset_index(drop=True)

            # Convert all columns to string type
            df = df.astype(str)

            # Convert DataFrame to records and ensure all keys are strings
            preview_rows = []
            for row in df.head(params.num_rows).to_dict(orient="records"):
                # Create a new dict with string keys
                string_row = {str(k): v for k, v in row.items()}
                preview_rows.append(string_row)

            logger.info(
                "Successfully generated data preview",
                num_preview_rows=len(preview_rows),
                num_columns=len(df.columns),
            )

            return DataPreviewOutput(columns=list(df.columns), rows=preview_rows)
        except Exception as e:
            logger.error("Error generating data preview", error=str(e))
            raise
