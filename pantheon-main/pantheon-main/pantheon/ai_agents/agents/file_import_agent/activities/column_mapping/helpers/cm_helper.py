import json
import os
from typing import Dict, Any, List, Tuple
import pandas as pd
import structlog
from pydantic import ValidationError

from pantheon.ai_agents.internal.llm_service.service import LLMService
from pantheon.ai_agents.internal.llm_service.enums.llmclient import (
    LLMModel,
    Role,
    ContentType,
    LLMClientType,
)
from ..schema.cm_schema import LLMResponse
from ..constants.cm_constants import (
    GET_COLUMN_MAPPINGS_PROMPT_PATH,
    ACCEPTED_FORMAT_PATH,
    SPECIAL_INSTRUCTIONS_PATH,
    COLUMN_MAPPING_EXAMPLE1_PATH,
    SAMPLE_DATA_EXAMPLE1_PATH,
    SAMPLE_OUTPUT1_PATH,
    COLUMN_MAPPING_EXAMPLE2_PATH,
    SAMPLE_DATA_EXAMPLE2_PATH,
    SAMPLE_OUTPUT2_PATH,
    ATTRIBUTE_METADATA,
)
from .cm_handle_dates import handle_date_attributes

logger = structlog.get_logger(__name__)


class ColumnMappingAgent:
    def __init__(self):
        self.llm_service = LLMService(client_type=LLMClientType.ANTHROPIC)
        self.system_prompt = self._load_file_content(GET_COLUMN_MAPPINGS_PROMPT_PATH)
        self.accepted_format = self._load_file_content(ACCEPTED_FORMAT_PATH)
        self.special_instructions = self._load_file_content(SPECIAL_INSTRUCTIONS_PATH)
        self.column_mapping_example1 = self._load_file_content(
            COLUMN_MAPPING_EXAMPLE1_PATH
        )
        self.sample_data_example1 = self._load_file_content(SAMPLE_DATA_EXAMPLE1_PATH)
        self.sample_output1 = self._load_file_content(SAMPLE_OUTPUT1_PATH)
        self.column_mapping_example2 = self._load_file_content(
            COLUMN_MAPPING_EXAMPLE2_PATH
        )
        self.sample_data_example2 = self._load_file_content(SAMPLE_DATA_EXAMPLE2_PATH)
        self.sample_output2 = self._load_file_content(SAMPLE_OUTPUT2_PATH)

    @staticmethod
    def _load_file_content(file_path: str) -> str:
        # Construct the correct path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        correct_path = os.path.join(
            current_dir, "..", "static", os.path.basename(file_path)
        )

        with open(correct_path, "r", encoding="utf-8") as file:
            return file.read()

    async def get_column_mappings(
        self,
        island_df: pd.DataFrame,
        column_info: Dict[str, Any],
        original_df: pd.DataFrame,
    ) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
        try:
            column_mapping = json.dumps(column_info, indent=2)
            df_sample = island_df.head(10)

            # Transpose the DataFrame and convert to CSV string
            sample_data_csv = df_sample.T.reset_index().to_csv(
                index=False, header=False
            )

            llm_message = self.system_prompt.format(
                ACCEPTED_FORMAT=self.accepted_format,
                SPECIAL_INSTRUCTIONS=self.special_instructions,
                COLUMN_MAPPING_EXAMPLE1=self.column_mapping_example1,
                SAMPLE_DATA_EXAMPLE1=self.sample_data_example1,
                SAMPLE_OUTPUT1=self.sample_output1,
                COLUMN_MAPPING_EXAMPLE2=self.column_mapping_example2,
                SAMPLE_DATA_EXAMPLE2=self.sample_data_example2,
                SAMPLE_OUTPUT2=self.sample_output2,
            )

            messages = [
                {Role.ROLE: Role.SYSTEM, ContentType.CONTENT: llm_message},
                {
                    Role.ROLE: Role.USER,
                    ContentType.CONTENT: [
                        {
                            ContentType.TYPE: ContentType.TEXT,
                            ContentType.TEXT: f"""
                                Inputs:
                                1. Column Mapping:
                                <column_mapping>
                                {column_mapping}
                                </column_mapping>

                                2. Sample Data (first few rows):
                                <sample_data>
                                {sample_data_csv}
                                </sample_data>
                            """,
                        }
                    ],
                },
            ]

            response = await self.llm_service.send_message_async(
                messages=messages, model=str(LLMModel.Claude3_5Sonnet)
            )

            response_json = json.loads(response.content)

            return self.extract_and_validate_llm_response(response_json, original_df)

        except Exception as e:
            logger.exception(
                "COLUMN_MAPPING_AGENT_ERROR_GETTING_COLUMN_MAPPINGS",
                error=str(e),
            )
            return [], [], []

    @staticmethod
    def extract_and_validate_llm_response(
        response_json: Dict[str, Any], df: pd.DataFrame
    ) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
        try:
            llm_response = LLMResponse.parse_obj(response_json)

            mapped_attributes = set(
                column["mapped_attribute"] for column in llm_response.mapped_columns
            )
            all_attributes = set(ATTRIBUTE_METADATA)
            unmapped_attributes = list(all_attributes - mapped_attributes)
            mapped_columns = llm_response.mapped_columns

            mapped_columns, unmapped_attributes, mapped_attributes = (
                handle_date_attributes(
                    df, mapped_columns, unmapped_attributes, mapped_attributes
                )
            )

            return (
                mapped_columns,
                unmapped_attributes,
                llm_response.errors,
            )

        except ValidationError as e:
            logger.error("Validation error in LLM response", error=str(e))
            raise ValueError("Invalid LLM response structure")
        except Exception as e:
            logger.error("Error processing LLM response", error=str(e))
            raise Exception(
                f"An error occurred while processing the response: {str(e)}"
            )
