from pantheon_v2.tools.common.pandas.tool import PandasTool
from pantheon_v2.tools.common.pandas.models import (
    FileToPandasInput,
    ConvertFileToDFOutput,
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

from pantheon_v2.tools.core.activity_registry import ActivityRegistry


@ActivityRegistry.register_activity(
    "Execute a Python function with resource constraints"
)
async def convert_file_to_df(params: FileToPandasInput) -> ConvertFileToDFOutput:
    """Execute a Python function with the given arguments"""
    tool = PandasTool()
    await tool.initialize()
    return await tool.convert_file_to_df(params)


@ActivityRegistry.register_activity("Detect tables and metadata in a CSV file")
async def detect_tables_and_metadata(
    params: DetectTablesAndMetadataInput,
) -> DetectTablesAndMetadataOutput:
    tool = PandasTool()
    await tool.initialize()
    return await tool.detect_tables_and_metadata(params)


@ActivityRegistry.register_activity("Add metadata columns to a DataFrame")
async def add_columns_to_df(
    params: AddMetadataColumnsInput,
) -> AddMetadataColumnsOutput:
    tool = PandasTool()
    await tool.initialize()
    return await tool.add_columns_to_df(params)


@ActivityRegistry.register_activity("Convert DataFrame to CSV format")
async def df_to_csv(params: DFToCSVInput) -> DFToCSVOutput:
    """Convert a DataFrame to CSV format with the given parameters"""
    tool = PandasTool()
    await tool.initialize()
    return await tool.df_to_csv(params)


@ActivityRegistry.register_activity("Convert DataFrame to Parquet format")
async def df_to_parquet(params: DFToParquetInput) -> DFToParquetOutput:
    """Convert a DataFrame to Parquet format with the given parameters"""
    tool = PandasTool()
    await tool.initialize()
    return await tool.df_to_parquet(params)


@ActivityRegistry.register_activity("Generate data preview from DataFrame JSON")
async def generate_data_preview(params: DataPreviewInput) -> DataPreviewOutput:
    """Generate a preview of the DataFrame data"""
    tool = PandasTool()
    await tool.initialize()
    return await tool.generate_data_preview(params)
