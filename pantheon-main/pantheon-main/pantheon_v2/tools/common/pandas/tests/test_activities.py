import pytest
import pandas as pd
from io import BytesIO

from pantheon_v2.tools.common.pandas.activities import (
    convert_file_to_df,
    detect_tables_and_metadata,
    add_columns_to_df,
    df_to_csv,
    df_to_parquet,
    generate_data_preview,
)
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


@pytest.fixture
def sample_df():
    return pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})


@pytest.fixture
def sample_df_json(sample_df):
    return sample_df.to_json(orient="split")


@pytest.fixture
def sample_excel_bytes():
    df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    excel_buffer.seek(0)
    return excel_buffer


@pytest.fixture
def sample_csv_bytes():
    csv_data = "A,B\n1,x\n2,y"
    return BytesIO(csv_data.encode())


@pytest.mark.asyncio
async def test_convert_file_to_df_excel():
    # Test Excel file conversion
    df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    excel_buffer.seek(0)

    input_params = FileToPandasInput(file_name="test.xlsx", file_content=excel_buffer)

    result = await convert_file_to_df(input_params)
    assert isinstance(result, ConvertFileToDFOutput)
    assert result.success is True
    assert isinstance(result.result, str)

    # Verify the DataFrame content
    result_df = pd.read_json(result.result, orient="split")
    assert len(result_df.columns) == 2  # Should have 2 columns
    assert len(result_df) == 3  # Should have 3 rows (header + 2 data rows)
    # Convert all values to strings for comparison
    result_values = result_df.astype(str).values.tolist()
    assert ["A", "B"] in result_values  # Header row
    assert ["1", "x"] in result_values  # First data row
    assert ["2", "y"] in result_values  # Second data row


@pytest.mark.asyncio
async def test_convert_file_to_df_csv():
    # Test CSV file conversion
    csv_data = "A,B\n1,x\n2,y"
    csv_buffer = BytesIO(csv_data.encode())

    input_params = FileToPandasInput(file_name="test.csv", file_content=csv_buffer)

    result = await convert_file_to_df(input_params)
    assert isinstance(result, ConvertFileToDFOutput)
    assert result.success is True

    # Verify the DataFrame content
    result_df = pd.read_json(result.result, orient="split")
    assert len(result_df.columns) == 2  # Should have 2 columns
    assert len(result_df) == 3  # Should have 3 rows (header + 2 data rows)
    # Convert all values to strings for comparison
    result_values = result_df.astype(str).values.tolist()
    assert ["A", "B"] in result_values
    assert ["1", "x"] in result_values
    assert ["2", "y"] in result_values


@pytest.mark.asyncio
async def test_convert_file_to_df_parquet(sample_df):
    # Create a parquet file
    parquet_buffer = BytesIO()
    sample_df.to_parquet(parquet_buffer)
    parquet_buffer.seek(0)

    input_params = FileToPandasInput(
        file_name="test.parquet", file_content=parquet_buffer
    )

    result = await convert_file_to_df(input_params)
    assert isinstance(result, ConvertFileToDFOutput)
    assert result.success is True

    # Verify the DataFrame content
    result_df = pd.read_json(result.result, orient="split")
    pd.testing.assert_frame_equal(result_df, sample_df)


@pytest.mark.asyncio
async def test_convert_file_to_df_unsupported():
    # Test unsupported file type
    input_params = FileToPandasInput(
        file_name="test.txt", file_content=BytesIO(b"some text")
    )

    result = await convert_file_to_df(input_params)
    assert isinstance(result, ConvertFileToDFOutput)
    assert result.success is False
    assert result.result is None


@pytest.mark.asyncio
async def test_detect_tables_and_metadata():
    # Create test data with tables and metadata
    df = pd.DataFrame(
        {
            0: ["Report Date:", "2023-01-01", "", "Column1", "100", "200"],
            1: ["", "", "", "Column2", "300", "400"],
        }
    )
    input_json = df.to_json(orient="split")

    input_params = DetectTablesAndMetadataInput(file_content=input_json)
    result = await detect_tables_and_metadata(input_params)

    assert isinstance(result, DetectTablesAndMetadataOutput)
    assert result.success is True
    assert result.table_df is not None
    assert result.metadata_df is not None

    # Verify table content
    table_df = pd.read_json(result.table_df, orient="split")
    assert len(table_df) == 3  # Header + 2 data rows

    # Verify metadata content
    metadata_df = pd.read_json(result.metadata_df, orient="split")
    assert len(metadata_df) > 0


@pytest.mark.asyncio
async def test_detect_tables_and_metadata_error():
    # Test with invalid JSON
    input_params = DetectTablesAndMetadataInput(file_content="invalid json")
    result = await detect_tables_and_metadata(input_params)

    assert isinstance(result, DetectTablesAndMetadataOutput)
    assert result.success is False
    assert result.table_df is None
    assert result.metadata_df is None


@pytest.mark.asyncio
async def test_add_columns_to_df():
    # Create test data
    df = pd.DataFrame({"Col1": ["Value1", "Value2"], "Col2": ["Value3", "Value4"]})
    input_json = df.to_json(orient="split")

    metadata = {"data": {"source": "test_source", "tags": ["tag1", "tag2"]}}

    input_params = AddMetadataColumnsInput(file_content=input_json, metadata=metadata)

    result = await add_columns_to_df(input_params)

    assert isinstance(result, AddMetadataColumnsOutput)
    assert result.success is True
    assert result.result_df is not None

    # Verify the result
    result_df = pd.read_json(result.result_df, orient="split")
    assert "source" in result_df.columns
    assert "tags_1" in result_df.columns
    assert "tags_2" in result_df.columns
    assert result_df["source"].iloc[0] == "test_source"
    assert result_df["tags_1"].iloc[0] == "tag1"


@pytest.mark.asyncio
async def test_add_columns_to_df_error():
    # Test with invalid JSON
    input_params = AddMetadataColumnsInput(
        file_content="invalid json", metadata={"data": {}}
    )

    result = await add_columns_to_df(input_params)
    assert isinstance(result, AddMetadataColumnsOutput)
    assert result.success is False
    assert result.result_df is None


@pytest.mark.asyncio
async def test_df_to_csv_string_headers():
    # Test with string headers
    df = pd.DataFrame({"Col1": ["Value1", "Value2"], "Col2": ["Value3", "Value4"]})
    input_json = df.to_json(orient="split")

    input_params = DFToCSVInput(file_content=input_json)
    result = await df_to_csv(input_params)

    assert isinstance(result, DFToCSVOutput)
    assert result.success is True
    assert isinstance(result.csv_content, BytesIO)

    # Verify CSV content
    result.csv_content.seek(0)
    csv_content = result.csv_content.read().decode("utf-8")
    assert "Col1,Col2" in csv_content
    assert "Value1,Value3" in csv_content


@pytest.mark.asyncio
async def test_df_to_csv_numeric_headers():
    # Test with numeric headers
    df = pd.DataFrame({0: ["Header1", "Value1"], 1: ["Header2", "Value2"]})
    input_json = df.to_json(orient="split")

    input_params = DFToCSVInput(file_content=input_json)
    result = await df_to_csv(input_params)

    assert isinstance(result, DFToCSVOutput)
    assert result.success is True
    assert isinstance(result.csv_content, BytesIO)

    # Verify CSV content
    result.csv_content.seek(0)
    csv_content = result.csv_content.read().decode("utf-8")
    assert "Header1,Header2" in csv_content
    assert "Value1,Value2" in csv_content


@pytest.mark.asyncio
async def test_df_to_csv_error():
    # Test with invalid JSON
    input_params = DFToCSVInput(file_content="invalid json")
    result = await df_to_csv(input_params)

    assert isinstance(result, DFToCSVOutput)
    assert result.success is False
    assert result.csv_content is None


# Existing tests...
@pytest.mark.asyncio
async def test_df_to_parquet():
    # Create test data
    df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
    input_json = df.to_json(orient="split")

    # Create input model
    input_params = DFToParquetInput(file_content=input_json)

    # Call the function
    result = await df_to_parquet(input_params)

    # Verify the result
    assert isinstance(result, DFToParquetOutput)
    assert result.success is True
    assert isinstance(result.parquet_content, BytesIO)

    # Verify the parquet content can be read back as a DataFrame
    result.parquet_content.seek(0)
    df_result = pd.read_parquet(result.parquet_content)
    pd.testing.assert_frame_equal(df_result, df)


@pytest.mark.asyncio
async def test_df_to_parquet_error():
    # Test with invalid JSON
    input_params = DFToParquetInput(file_content="invalid json")

    # Call the function
    result = await df_to_parquet(input_params)

    # Verify error handling
    assert isinstance(result, DFToParquetOutput)
    assert result.success is False
    assert result.parquet_content is None


@pytest.mark.asyncio
async def test_generate_data_preview_numeric_headers():
    # Create test data with numeric headers
    df = pd.DataFrame(
        {0: ["Header1", "Value1", "Value2"], 1: ["Header2", "Value3", "Value4"]}
    )
    input_json = df.to_json(orient="split")

    # Create input model
    input_params = DataPreviewInput(df_json=input_json, num_rows=2)

    # Call the function
    result = await generate_data_preview(input_params)

    # Verify the result
    assert isinstance(result, DataPreviewOutput)
    assert "Header1" in result.columns
    assert "Header2" in result.columns
    assert len(result.rows) == 2
    assert result.rows[0]["Header1"] == "Value1"
    assert result.rows[0]["Header2"] == "Value3"


@pytest.mark.asyncio
async def test_generate_data_preview_string_headers():
    # Create test data with string headers
    df = pd.DataFrame({"Col1": ["Value1", "Value2"], "Col2": ["Value3", "Value4"]})
    input_json = df.to_json(orient="split")

    # Create input model
    input_params = DataPreviewInput(df_json=input_json, num_rows=1)

    # Call the function
    result = await generate_data_preview(input_params)

    # Verify the result
    assert isinstance(result, DataPreviewOutput)
    assert "Col1" in result.columns
    assert "Col2" in result.columns
    assert len(result.rows) == 1
    assert result.rows[0]["Col1"] == "Value1"
    assert result.rows[0]["Col2"] == "Value3"


@pytest.mark.asyncio
async def test_generate_data_preview_error():
    # Test with invalid JSON
    input_params = DataPreviewInput(df_json="invalid json", num_rows=2)

    # Call the function and expect an exception
    with pytest.raises(Exception):
        await generate_data_preview(input_params)


# Test PandasTool class methods directly
@pytest.mark.asyncio
async def test_pandas_tool_df_to_parquet():
    from pantheon_v2.tools.common.pandas.tool import PandasTool

    # Create test data
    df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
    input_json = df.to_json(orient="split")

    # Create tool instance
    tool = PandasTool()
    await tool.initialize()

    # Create input model
    input_params = DFToParquetInput(file_content=input_json)

    # Call the method
    result = await tool.df_to_parquet(input_params)

    # Verify the result
    assert isinstance(result, DFToParquetOutput)
    assert result.success is True
    assert isinstance(result.parquet_content, BytesIO)

    # Verify the parquet content
    result.parquet_content.seek(0)
    df_result = pd.read_parquet(result.parquet_content)
    pd.testing.assert_frame_equal(df_result, df)


@pytest.mark.asyncio
async def test_pandas_tool_generate_data_preview():
    from pantheon_v2.tools.common.pandas.tool import PandasTool

    # Create test data
    df = pd.DataFrame({"Col1": ["Value1", "Value2"], "Col2": ["Value3", "Value4"]})
    input_json = df.to_json(orient="split")

    # Create tool instance
    tool = PandasTool()
    await tool.initialize()

    # Create input model
    input_params = DataPreviewInput(df_json=input_json, num_rows=2)

    # Call the method
    result = await tool.generate_data_preview(input_params)

    # Verify the result
    assert isinstance(result, DataPreviewOutput)
    assert "Col1" in result.columns
    assert "Col2" in result.columns
    assert len(result.rows) == 2
    assert result.rows[0]["Col1"] == "Value1"
    assert result.rows[0]["Col2"] == "Value3"
