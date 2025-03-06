import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from pantheon_v2.processes.common.table_detection_workflow.table_detection_workflow import (
    TableDetectionWorkflow,
)
from pantheon_v2.processes.common.table_detection_workflow.models import (
    TableDetectionInput,
    TableDetectionOutput,
    ColumnMappingResult,
)

from pantheon_v2.tools.common.pandas.models import (
    ConvertFileToDFOutput,
    DetectTablesAndMetadataOutput,
    DataPreviewOutput,
)

from pantheon_v2.tools.external.s3.models import (
    DownloadFromS3Output,
    UploadToS3Output,
)

from pantheon_v2.processes.common.table_detection_workflow.business_logic.models import (
    ColumnMappingOutput,
    MissingColumns,
    LLMCallOutput,
    MetadataOutput,
)


class TestTableDetectionWorkflow:
    @pytest.fixture
    def workflow(self):
        return TableDetectionWorkflow()

    @pytest.fixture
    def mock_s3_content(self):
        return b"mock file content"

    @pytest.fixture
    def mock_df(self):
        return pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

    @pytest.fixture
    def mock_target_df(self):
        return pd.DataFrame({"target_col1": [], "target_col2": []})

    @pytest.mark.asyncio
    async def test_table_detection_workflow_basic(
        self, workflow, mock_s3_content, mock_df
    ):
        """Test basic workflow execution without output format"""

        def mock_activity_response(*args, **kwargs):
            if args[0].__name__ == "download_from_s3":
                return DownloadFromS3Output(content=mock_s3_content)
            elif args[0].__name__ == "convert_file_to_df":
                return ConvertFileToDFOutput(
                    success=True, result=mock_df.to_json(orient="split")
                )
            elif args[0].__name__ == "detect_tables_and_metadata":
                return DetectTablesAndMetadataOutput(
                    success=True,
                    table_df=mock_df.to_json(orient="split"),
                    metadata_df=None,
                )
            elif args[0].__name__ == "df_to_parquet":
                return MagicMock(parquet_content=b"mock parquet content")
            elif args[0].__name__ == "upload_to_s3":
                return UploadToS3Output(
                    s3_url="s3://bucket/path/file.parquet",
                    https_url="https://bucket.s3.amazonaws.com/path/file.parquet",
                    metadata={"content-type": "application/parquet"},
                )
            elif args[0].__name__ == "generate_data_preview":
                return DataPreviewOutput(
                    columns=["col1", "col2"],
                    rows=[{"col1": 1, "col2": "a"}, {"col1": 2, "col2": "b"}],
                )
            return None

        with patch(
            "pantheon_v2.processes.common.table_detection_workflow.table_detection_workflow.workflow.execute_activity",
            side_effect=mock_activity_response,
        ):
            result = await workflow.run(
                TableDetectionInput(
                    source_bucket="test-bucket",
                    source_file_path="test.csv",
                )
            )

        assert isinstance(result, TableDetectionOutput)
        assert result.transformed_data_bucket == "bucket"
        assert result.transformed_data_path == "path/file.parquet"
        assert result.column_mapping is None
        assert result.data_preview.columns == ["col1", "col2"]
        assert len(result.data_preview.rows) == 2

    @pytest.mark.asyncio
    async def test_table_detection_workflow_with_output_format(
        self, workflow, mock_s3_content, mock_df, mock_target_df
    ):
        """Test workflow execution with output format mapping"""

        column_mapping = {
            "mapped_columns": [
                {
                    "source_column": "col1",
                    "target_column": "target_col1",
                    "confidence": 0.95,
                    "mapping_reason": "Exact match",
                }
            ],
            "missing_columns": {"source": [], "target": ["target_col2"]},
            "document_type": "test",
            "confidence": 0.9,
        }

        def mock_activity_response(*args, **kwargs):
            if args[0].__name__ == "download_from_s3":
                return DownloadFromS3Output(content=mock_s3_content)
            elif args[0].__name__ == "convert_file_to_df":
                df_to_use = mock_target_df if "format" in kwargs else mock_df
                return ConvertFileToDFOutput(
                    success=True, result=df_to_use.to_json(orient="split")
                )
            elif args[0].__name__ == "detect_tables_and_metadata":
                return DetectTablesAndMetadataOutput(
                    success=True,
                    table_df=mock_df.to_json(orient="split"),
                    metadata_df=None,
                )
            elif args[0].__name__ == "execute_code":
                # Check if this is a column_mapping call - safely access the function property
                if (
                    len(args) > 1
                    and hasattr(args[1], "function")
                    and isinstance(args[1].function, str)
                    and args[1].function.endswith("execute_column_mapping")
                ):
                    # Create a mock with the appropriate structure
                    column_mapping_output = ColumnMappingOutput(
                        mapped_columns=[
                            {
                                "source_column": "col1",
                                "target_column": "target_col1",
                                "confidence": 0.95,
                                "mapping_reason": "Exact match",
                            }
                        ],
                        missing_columns=MissingColumns(
                            source=[],
                            target=["target_col2"],
                        ),
                        document_type="test",
                        confidence=0.9,
                    )
                    column_mapping_mock = MagicMock()
                    column_mapping_mock.result = column_mapping_output
                    return column_mapping_mock
                return MagicMock(
                    result=ColumnMappingOutput(
                        mapped_columns=column_mapping["mapped_columns"],
                        missing_columns=MissingColumns(
                            source=column_mapping["missing_columns"]["source"],
                            target=column_mapping["missing_columns"]["target"],
                        ),
                        document_type=column_mapping["document_type"],
                        confidence=column_mapping["confidence"],
                    )
                )
            elif args[0].__name__ == "df_to_parquet":
                return MagicMock(parquet_content=b"mock parquet content")
            elif args[0].__name__ == "upload_to_s3":
                return UploadToS3Output(
                    s3_url="s3://bucket/path/file.parquet",
                    https_url="https://bucket.s3.amazonaws.com/path/file.parquet",
                    metadata={"content-type": "application/parquet"},
                )
            elif args[0].__name__ == "generate_data_preview":
                return DataPreviewOutput(
                    columns=["col1", "col2"],
                    rows=[{"col1": 1, "col2": "a"}, {"col1": 2, "col2": "b"}],
                )
            return None

        with patch(
            "pantheon_v2.processes.common.table_detection_workflow.table_detection_workflow.workflow.execute_activity",
            side_effect=mock_activity_response,
        ):
            result = await workflow.run(
                TableDetectionInput(
                    source_bucket="test-bucket",
                    source_file_path="test.csv",
                    output_format_bucket="format-bucket",
                    output_format_path="format.csv",
                )
            )

        assert isinstance(result, TableDetectionOutput)
        assert result.transformed_data_bucket == "bucket"
        assert result.transformed_data_path == "path/file.parquet"
        assert isinstance(result.column_mapping, ColumnMappingResult)
        assert len(result.column_mapping.mapped_columns) == 1
        assert result.column_mapping.mapped_columns[0].source_column == "col1"
        assert result.column_mapping.mapped_columns[0].target_column == "target_col1"
        assert result.column_mapping.mapped_columns[0].confidence == 0.95
        assert result.column_mapping.mapped_columns[0].mapping_reason == "Exact match"
        assert set(result.column_mapping.missing_columns.target) == {
            "target_col1",
            "target_col2",
        }
        assert result.data_preview.columns == ["col1", "col2"]

    @pytest.mark.asyncio
    async def test_table_detection_workflow_with_metadata(
        self, workflow, mock_s3_content, mock_df
    ):
        """Test workflow execution with metadata processing"""
        metadata_df = pd.DataFrame({"metadata_col": ["value1", "value2"]})
        metadata_result = {"extracted_data": {"key": "value"}}

        def mock_activity_response(*args, **kwargs):
            if args[0].__name__ == "download_from_s3":
                return DownloadFromS3Output(content=mock_s3_content)
            elif args[0].__name__ == "convert_file_to_df":
                return ConvertFileToDFOutput(
                    success=True, result=mock_df.to_json(orient="split")
                )
            elif args[0].__name__ == "detect_tables_and_metadata":
                return DetectTablesAndMetadataOutput(
                    success=True,
                    table_df=mock_df.to_json(orient="split"),
                    metadata_df=metadata_df.to_json(orient="split"),
                )
            elif args[0].__name__ == "execute_code":
                # Check if this is a metadata extraction call - safely access the function property
                if (
                    len(args) > 1
                    and hasattr(args[1], "function")
                    and isinstance(args[1].function, str)
                    and args[1].function.endswith("extract_metadata")
                ):
                    # Create a mock with the appropriate structure for metadata extraction
                    metadata_mock = MagicMock()
                    metadata_mock.result = LLMCallOutput(
                        extracted_data=MetadataOutput(
                            data=metadata_result["extracted_data"]
                        )
                    )
                    return metadata_mock
                # For other execute_code calls, return a proper structured object
                return MagicMock(
                    result=LLMCallOutput(
                        extracted_data=MetadataOutput(
                            data=metadata_result["extracted_data"]
                        )
                    )
                )
            elif args[0].__name__ == "add_columns_to_df":
                return MagicMock(
                    success=True, result_df=mock_df.to_json(orient="split")
                )
            elif args[0].__name__ == "df_to_parquet":
                return MagicMock(parquet_content=b"mock parquet content")
            elif args[0].__name__ == "upload_to_s3":
                return UploadToS3Output(
                    s3_url="s3://bucket/path/file.parquet",
                    https_url="https://bucket.s3.amazonaws.com/path/file.parquet",
                    metadata={"content-type": "application/parquet"},
                )
            elif args[0].__name__ == "generate_data_preview":
                return DataPreviewOutput(
                    columns=["col1", "col2"],
                    rows=[{"col1": 1, "col2": "a"}, {"col1": 2, "col2": "b"}],
                )
            return None

        with patch(
            "pantheon_v2.processes.common.table_detection_workflow.table_detection_workflow.workflow.execute_activity",
            side_effect=mock_activity_response,
        ):
            result = await workflow.run(
                TableDetectionInput(
                    source_bucket="test-bucket",
                    source_file_path="test.csv",
                )
            )

        assert isinstance(result, TableDetectionOutput)
        assert result.extracted_metadata == {"data": {"key": "value"}}
        assert result.data_preview.columns == ["col1", "col2"]

    @pytest.mark.asyncio
    async def test_table_detection_workflow_validation_error(self, workflow):
        """Test workflow input validation"""
        with pytest.raises(ValueError):
            await workflow.run(
                TableDetectionInput(
                    source_bucket="",  # Empty source bucket
                    source_file_path="test.csv",
                )
            )

        with pytest.raises(ValueError):
            await workflow.run(
                TableDetectionInput(
                    source_bucket="test-bucket",
                    source_file_path="",  # Empty source file path
                )
            )

        with pytest.raises(ValueError):
            await workflow.run(
                TableDetectionInput(
                    source_bucket="test-bucket",
                    source_file_path="test.csv",
                    output_format_path="format.csv",  # Missing output format bucket
                )
            )

    @pytest.mark.asyncio
    async def test_table_detection_workflow_failed_detection(
        self, workflow, mock_s3_content, mock_df
    ):
        """Test workflow when table detection fails"""

        def mock_activity_response(*args, **kwargs):
            if args[0].__name__ == "download_from_s3":
                return DownloadFromS3Output(content=mock_s3_content)
            elif args[0].__name__ == "convert_file_to_df":
                return ConvertFileToDFOutput(
                    success=True, result=mock_df.to_json(orient="split")
                )
            elif args[0].__name__ == "detect_tables_and_metadata":
                return DetectTablesAndMetadataOutput(
                    success=False,  # Failed detection
                    table_df=None,
                    metadata_df=None,
                )
            return None

        with patch(
            "pantheon_v2.processes.common.table_detection_workflow.table_detection_workflow.workflow.execute_activity",
            side_effect=mock_activity_response,
        ):
            result = await workflow.run(
                TableDetectionInput(
                    source_bucket="test-bucket",
                    source_file_path="test.csv",
                )
            )

        assert result is None
