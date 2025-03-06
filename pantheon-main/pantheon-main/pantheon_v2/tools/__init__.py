from pantheon_v2.tools.common.pdf_parser.activities import parse_pdf
from pantheon_v2.tools.common.code_executor.activities import execute_code
from pantheon_v2.tools.common.contract_data_extracter.activities import (
    extract_contract_data,
)
from pantheon_v2.tools.core.internal_data_repository.activities import (
    query_internal_relational_data,
    insert_internal_relational_data,
    update_internal_relational_data,
    query_internal_blob_storage,
    query_internal_blob_storage_folder,
    upload_internal_blob_storage,
)
from pantheon_v2.tools.external.snowflake.activities import (
    query_snowflake_data,
    insert_snowflake_data,
    update_snowflake_data,
    delete_snowflake_data,
)
from pantheon_v2.tools.external.slack.activities import send_slack_message
from pantheon_v2.tools.common.pandas.activities import (
    convert_file_to_df,
    detect_tables_and_metadata,
    add_columns_to_df,
    df_to_csv,
    df_to_parquet,
    generate_data_preview,
)
from pantheon_v2.tools.external.gcs.activities import download_from_gcs
from pantheon_v2.tools.external.s3.activities import (
    download_from_s3,
    upload_to_s3,
    download_folder_from_s3,
)

from pantheon_v2.tools.common.ocr.activities import extract_ocr_data
from pantheon_v2.tools.common.ai_model_hub.activities import (
    generate_llm_model_response,
    generate_embeddings,
)

from pantheon_v2.tools.external.gmail.activities import (
    search_messages,
    get_message_eml,
)
from pantheon_v2.tools.common.email_parser.activities import parse_email

exposed_activities = [
    # Code Executor Tool
    execute_code,
    # Contract Data Extracter Tool
    extract_contract_data,
    # PDF Parser Tool
    parse_pdf,
    # Email Parser Tool
    parse_email,
    # Internal Data Repository Tool
    query_internal_relational_data,
    insert_internal_relational_data,
    update_internal_relational_data,
    query_internal_blob_storage,
    query_internal_blob_storage_folder,
    upload_internal_blob_storage,
    # Snowflake Tool
    query_snowflake_data,
    insert_snowflake_data,
    update_snowflake_data,
    delete_snowflake_data,
    # Slack Tool
    send_slack_message,
    # GCS Tool
    download_from_gcs,
    # Pandas Tool
    convert_file_to_df,
    detect_tables_and_metadata,
    add_columns_to_df,
    df_to_csv,
    df_to_parquet,
    generate_data_preview,
    # S3 Tool
    download_from_s3,
    upload_to_s3,
    download_folder_from_s3,
    # OCR Tool
    extract_ocr_data,
    # Gmail Tool
    search_messages,
    get_message_eml,
    # LLM Model Tool
    generate_llm_model_response,
    generate_embeddings,
]
