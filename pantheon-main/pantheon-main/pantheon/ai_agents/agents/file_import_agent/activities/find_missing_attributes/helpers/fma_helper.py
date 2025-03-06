import pandas as pd
import json
from typing import Dict, List, Any, Tuple

import structlog

from pantheon.ai_agents.internal.llm_service.service import LLMService
from pantheon.ai_agents.internal.llm_service.enums.llmclient import (
    LLMModel,
    Role,
    ContentType,
    LLMClientType,
)
from ..constants.fma_constants import (
    DETECT_MISSING_ATTRIBUTES_FILE_PATH,
    ACCEPTED_FORMAT_PATH,
)
from pantheon.ai_agents.agents.file_import_agent.activities.find_missing_attributes.helpers.fma_tools import (
    load_file_content,
    parse_region,
    is_entire_dataframe,
    calculate_remaining_region,
    clean_df,
)

logger = structlog.get_logger(__name__)


class MissingAttributesAgent:
    def __init__(self):
        self.llm_service = LLMService(client_type=LLMClientType.ANTHROPIC)
        self.detect_missing_attributes_prompt = load_file_content(
            DETECT_MISSING_ATTRIBUTES_FILE_PATH
        )
        self.accepted_format = load_file_content(ACCEPTED_FORMAT_PATH)

    async def detect_missing_attributes(
        self, original_df: pd.DataFrame, region: str, unmapped_attributes: List[str]
    ) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, Any]]:
        try:
            match = parse_region(region)
            if not match:
                return [], unmapped_attributes, {"opening_balance": None}

            start_col, start_row, end_col, end_row = match
            if is_entire_dataframe(start_row, start_col, end_row, end_col, original_df):
                return [], unmapped_attributes, {"opening_balance": None}

            remaining_df = calculate_remaining_region(
                original_df, start_row, start_col, end_row, end_col
            )

            cleaned_df = clean_df(remaining_df)
            cleaned_data_str = cleaned_df.to_string(
                index=False, header=False, na_rep=""
            )

            formatted_prompt = self._format_prompt(
                unmapped_attributes, cleaned_data_str
            )
            response_json = await self._get_llm_response(formatted_prompt)

            validated_response, opening_balance = self._validate_llm_response(
                response_json, region
            )

            return (
                validated_response,
                [
                    attr
                    for attr in unmapped_attributes
                    if attr not in [item["name"] for item in validated_response]
                ],
                opening_balance,
            )

        except Exception as e:
            logger.exception(
                "MISSING_ATTRIBUTES_AGENT_ERROR_DETECTING_MISSING_ATTRIBUTES",
                error=str(e),
            )
            return [], unmapped_attributes, {"opening_balance": None}

    def _format_prompt(
        self, unmapped_attributes: List[str], cleaned_data_str: str
    ) -> str:
        return self.detect_missing_attributes_prompt.format(
            unmapped_attributes=unmapped_attributes,
            ACCEPTED_FORMAT=self.accepted_format,
            cleaned_data_str=cleaned_data_str,
        )

    async def _get_llm_response(self, formatted_prompt: str) -> Dict[str, Any]:
        messages = [
            {
                Role.ROLE: Role.USER,
                ContentType.CONTENT: [
                    {
                        ContentType.TYPE: ContentType.TEXT,
                        ContentType.TEXT: formatted_prompt,
                    }
                ],
            }
        ]

        response = await self.llm_service.send_message_async(
            messages=messages, model=str(LLMModel.Claude3_5Sonnet)
        )

        return json.loads(response.content)

    @staticmethod
    def _validate_llm_response(
        response_json: Dict[str, Dict[str, str]],
        region: str,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        validated_response = []
        opening_balance = None

        for attr, attr_data in response_json.items():
            if "value" in attr_data and "attribute_type" in attr_data:
                if attr == "opening_balance":
                    opening_balance = {"opening_balance": attr_data["value"]}
                else:
                    validated_response.append(
                        {
                            "name": attr,
                            "value": attr_data["value"],
                            "region": region,
                            "attribute_type": attr_data["attribute_type"],
                        }
                    )

        if opening_balance is None:
            opening_balance = {"opening_balance": None}

        return validated_response, opening_balance
