from pantheon_v2.processes.core.registry import WorkflowRegistry
from temporalio import workflow

# Import activity, passing it through the sandbox without reloading the module
with workflow.unsafe.imports_passed_through():
    import structlog
    from datetime import timedelta

    logger = structlog.get_logger(__name__)

    from pantheon_v2.tools.external.s3.models import (
        DownloadFromS3Input,
        UploadToS3Input,
    )
    from pantheon_v2.tools.external.s3.activities import download_from_s3, upload_to_s3
    from pantheon_v2.utils.s3_utils import extract_s3_info
    from pantheon_v2.utils.path_utils import sanitize_filename

    from pantheon_v2.tools.common.pandas.models import (
        FileToPandasInput,
        DetectTablesAndMetadataInput,
        AddMetadataColumnsInput,
        DataPreviewInput,
        DFToParquetInput,
    )
    from pantheon_v2.tools.common.pandas.activities import (
        convert_file_to_df,
        detect_tables_and_metadata,
        add_columns_to_df,
        generate_data_preview,
        df_to_parquet,
    )

    from pantheon_v2.tools.common.code_executor.models import ExecuteCodeParams
    from pantheon_v2.tools.common.code_executor.config import CodeExecutorConfig
    from pantheon_v2.tools.common.code_executor.activities import execute_code
    from pantheon_v2.utils.type_utils import get_fqn
    from pantheon_v2.processes.common.table_detection_workflow.business_logic.extract_metadata import (
        extract_metadata,
    )
    from pantheon_v2.processes.common.table_detection_workflow.business_logic.column_mapping_llm_call import (
        execute_column_mapping,
    )
    from pantheon_v2.processes.common.table_detection_workflow.business_logic.constants import (
        MetadataMode,
    )
    from pantheon_v2.processes.common.table_detection_workflow.constants import (
        DEFAULT_S3_BUCKET,
        DEFAULT_OUTPUT_FILE_PATH,
        DEFAULT_OUTPUT_FILE_EXTENSION,
    )

    from pantheon_v2.processes.common.table_detection_workflow.business_logic.models import (
        ColumnMappingInput,
        MissingColumns,
        LLMCallInput,
    )
    from pantheon_v2.processes.common.table_detection_workflow.models import (
        TableDetectionInput,
        TableDetectionOutput,
        ColumnMappingResult,
        DataPreview,
    )


@WorkflowRegistry.register_workflow_defn(
    "Workflow that detects tables and metadata from a file and returns a structured table output as a parquet file",
    labels=["common"],
)
class TableDetectionWorkflow:
    """
    A workflow for detecting and processing tables from input files, with optional output format mapping.

    This workflow performs the following steps:
    1. Downloads and validates input files from S3
    2. Detects tables and metadata in the input file
    3. Performs column mapping if an output format is provided
    4. Extracts metadata using LLM
    5. Generates a data preview
    6. Uploads the processed file back to S3
    """

    def __init__(self):
        self.state = {}

    @WorkflowRegistry.register_workflow_run
    async def run(self, input_data: TableDetectionInput) -> TableDetectionOutput:
        """
        Execute the table detection workflow.

        Args:
            input_data: TableDetectionInput containing file paths and processing parameters

        Returns:
            TableDetectionOutput containing processed data location, column mapping, metadata, and preview
        """
        logger.info("Starting Table Detection Workflow")

        # Step 1: Validate and process input files
        source_bucket, source_filename, output_format_filename, output_format_bucket = (
            self._validate_and_extract_file_info(input_data)
        )

        # Step 2: Download and process source file
        processed_df, metadata_df = await self._process_source_file(
            source_bucket, source_filename
        )
        if not processed_df:
            return None

        # Step 3: Process output format if provided
        target_df = None
        column_mapping_result = None
        unmapped_target_columns = None
        if output_format_filename:
            (
                target_df,
                column_mapping_result,
                processed_df,
                unmapped_target_columns,
            ) = await self._process_output_format(
                output_format_filename, processed_df, output_format_bucket
            )

        # Step 4: Process metadata if available
        metadata_extraction_result = None
        if metadata_df is not None:
            processed_df, metadata_extraction_result = await self._process_metadata(
                metadata_df, processed_df, unmapped_target_columns
            )

        # Step 5: Convert and upload processed data
        transformed_bucket, transformed_path = await self._convert_and_upload_data(
            processed_df, source_filename
        )

        # Step 6: Generate data preview and prepare final output
        preview_result = await self._generate_preview(processed_df)
        final_column_mapping = self._prepare_final_column_mapping(
            output_format_filename, column_mapping_result, preview_result
        )

        # Return workflow output with separate bucket and path
        return TableDetectionOutput(
            transformed_data_bucket=transformed_bucket,
            transformed_data_path=transformed_path,
            column_mapping=final_column_mapping,
            extracted_metadata=metadata_extraction_result.result.extracted_data.model_dump()
            if metadata_extraction_result is not None
            else None,
            data_preview=DataPreview(
                columns=preview_result.columns, rows=preview_result.rows
            ),
        )

    def _validate_and_extract_file_info(
        self, input_data: TableDetectionInput
    ) -> tuple[str, str, str | None, str | None]:
        """Validate input paths and extract file information."""
        # Source file validation
        if not input_data.source_file_path or not input_data.source_bucket:
            raise ValueError("source_file_path and source_bucket are required")

        # Output format validation
        output_format_filename = None
        output_format_bucket = None
        if input_data.output_format_path:
            if not input_data.output_format_bucket:
                raise ValueError(
                    "output_format_bucket is required when output_format_path is provided"
                )
            output_format_filename = input_data.output_format_path
            output_format_bucket = input_data.output_format_bucket

        return (
            input_data.source_bucket,
            input_data.source_file_path,
            output_format_filename,
            output_format_bucket,
        )

    async def _process_source_file(self, source_bucket: str, source_filename: str):
        """Download and process the source file."""
        source_file_content = await workflow.execute_activity(
            download_from_s3,
            args=[
                DownloadFromS3Input(
                    bucket_name=source_bucket, file_name=source_filename
                )
            ],
            start_to_close_timeout=timedelta(minutes=10),
        )

        source_df_conversion = await workflow.execute_activity(
            convert_file_to_df,
            args=[
                FileToPandasInput(
                    file_content=source_file_content.content, file_name=source_filename
                )
            ],
            start_to_close_timeout=timedelta(minutes=10),
        )

        table_detection_result = await workflow.execute_activity(
            detect_tables_and_metadata,
            args=[
                DetectTablesAndMetadataInput(file_content=source_df_conversion.result)
            ],
            start_to_close_timeout=timedelta(minutes=10),
        )

        if not table_detection_result.success:
            logger.error("Table detection failed")
            return None, None

        return table_detection_result.table_df, table_detection_result.metadata_df

    async def _process_output_format(
        self, output_format_filename: str, processed_df, output_format_bucket: str
    ):
        """Process output format template and perform column mapping."""
        format_file_content = await workflow.execute_activity(
            download_from_s3,
            args=[
                DownloadFromS3Input(
                    bucket_name=output_format_bucket,
                    file_name=output_format_filename,
                ),
            ],
            start_to_close_timeout=timedelta(minutes=10),
        )

        target_df_conversion = await workflow.execute_activity(
            convert_file_to_df,
            args=[
                FileToPandasInput(
                    file_content=format_file_content.content,
                    file_name=output_format_filename,
                )
            ],
            start_to_close_timeout=timedelta(minutes=10),
        )
        target_df = target_df_conversion.result

        logger.info("Executing column mapping between source and target formats")
        column_mapping_result = await workflow.execute_activity(
            execute_code,
            args=[
                CodeExecutorConfig(timeout_seconds=30),
                ExecuteCodeParams(
                    function=get_fqn(execute_column_mapping),
                    args=(
                        ColumnMappingInput(
                            source_df=processed_df, target_df=target_df, sample_rows=3
                        ).dict(),
                    ),
                ),
            ],
            start_to_close_timeout=timedelta(minutes=1),
        )

        # Access missing_columns.target directly from the BaseModel
        unmapped_target_columns = column_mapping_result.result.missing_columns.target

        if column_mapping_result.result.normalized_df:
            processed_df = column_mapping_result.result.normalized_df
            logger.info("Updated processed_df with normalized columns")

        return target_df, column_mapping_result, processed_df, unmapped_target_columns

    async def _process_metadata(
        self, metadata_df, processed_df, unmapped_target_columns
    ):
        """Process metadata and add metadata columns to DataFrame."""
        if metadata_df is None:
            return processed_df, None

        llm_input = LLMCallInput(
            metadata_df=str(metadata_df),
            mode=MetadataMode.TARGETED if unmapped_target_columns else MetadataMode.ALL,
            target_attributes=unmapped_target_columns,
        )

        metadata_extraction_result = await workflow.execute_activity(
            execute_code,
            args=[
                CodeExecutorConfig(timeout_seconds=30),
                ExecuteCodeParams(
                    function=get_fqn(extract_metadata), args=(llm_input.dict(),)
                ),
            ],
            start_to_close_timeout=timedelta(minutes=1),
        )

        logger.info(
            "Extracted metadata",
            metadata=metadata_extraction_result.result.extracted_data,
            mode=llm_input.mode,
            target_attributes=llm_input.target_attributes
            if llm_input.target_attributes
            else None,
        )

        metadata_columns_result = await workflow.execute_activity(
            add_columns_to_df,
            args=[
                AddMetadataColumnsInput(
                    file_content=processed_df,
                    metadata=metadata_extraction_result.result.extracted_data.model_dump(),
                )
            ],
            start_to_close_timeout=timedelta(minutes=1),
        )

        if metadata_columns_result.success:
            logger.info("Successfully added metadata columns to table")
            return metadata_columns_result.result_df, metadata_extraction_result

        return processed_df, metadata_extraction_result

    async def _convert_and_upload_data(self, processed_df, source_filename: str):
        """Convert DataFrame to Parquet and upload to S3."""
        parquet_conversion = await workflow.execute_activity(
            df_to_parquet,
            args=[DFToParquetInput(file_content=processed_df)],
            start_to_close_timeout=timedelta(minutes=1),
        )

        # Generate path for the transformed data using sanitized source filename
        sanitized_name = sanitize_filename(
            source_filename, DEFAULT_OUTPUT_FILE_EXTENSION
        )
        transformed_data_path = f"{DEFAULT_OUTPUT_FILE_PATH}/{sanitized_name}"

        upload_result = await workflow.execute_activity(
            upload_to_s3,
            args=[
                UploadToS3Input(
                    bucket_name=DEFAULT_S3_BUCKET,
                    file_name=transformed_data_path,
                    blob=parquet_conversion.parquet_content,
                    content_type="application/parquet",
                ),
            ],
            start_to_close_timeout=timedelta(minutes=10),
        )

        # Extract bucket and path from the upload result
        bucket, path = extract_s3_info(upload_result.s3_url)
        return bucket, path

    async def _generate_preview(self, processed_df):
        """Generate data preview for output."""
        return await workflow.execute_activity(
            generate_data_preview,
            args=[DataPreviewInput(df_json=processed_df, num_rows=50)],
            start_to_close_timeout=timedelta(minutes=1),
        )

    def _prepare_final_column_mapping(
        self, output_format_filename, column_mapping_result, preview_result
    ):
        """Prepare final column mapping with updated information."""
        if not output_format_filename or not column_mapping_result:
            return None

        original_mapping = column_mapping_result.result
        final_available_columns = set(preview_result.columns)
        mapped_target_columns = {
            m.target_column for m in original_mapping.mapped_columns
        }
        all_target_columns = mapped_target_columns.union(
            set(
                original_mapping.missing_columns.target
                if original_mapping.missing_columns
                else []
            )
        )
        updated_missing_target = [
            col for col in all_target_columns if col not in final_available_columns
        ]

        return ColumnMappingResult(
            mapped_columns=original_mapping.mapped_columns,
            missing_columns=MissingColumns(source=[], target=updated_missing_target),
            document_type=original_mapping.document_type,
            confidence=original_mapping.confidence,
        )
