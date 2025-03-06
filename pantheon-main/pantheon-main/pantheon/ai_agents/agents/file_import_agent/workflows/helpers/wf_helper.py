import pandas as pd
from typing import Dict, Any, List, Tuple

from pantheon.ai_agents.agents.fileimport_agent.utils.utils import (
    detect_largest_island,
    clean_dataframe,
    find_header_row_and_columns,
)
from pantheon.ai_agents.agents.fileimport_agent.helper_agents.clean_credit_debit import (
    clean_credit_debit,
)
from pantheon.ai_agents.agents.fileimport_agent.constants.fileimport_agent_constants import (
    CREDIT,
    DEBIT,
)

import structlog

logger = structlog.get_logger(__name__)


class FileImportTool:
    def __init__(self, column_mapping_agent, missing_attributes_agent):
        self.column_mapping_agent = column_mapping_agent
        self.missing_attributes_agent = missing_attributes_agent

    def detect_island_and_clean(
        self, df: pd.DataFrame, start_row: int
    ) -> Tuple[str, pd.DataFrame]:
        region, island_df = detect_largest_island(df, start_row)
        island_df, region = clean_dataframe(island_df, region, 0.1)
        return region, island_df

    def find_header_and_columns(
        self, island_df: pd.DataFrame, region: str, start_row: int
    ) -> Tuple:
        return find_header_row_and_columns(island_df, 10, region, start_row)

    async def get_column_mappings(
        self, island_df: pd.DataFrame, column_info: List
    ) -> Tuple:
        return await self.column_mapping_agent.get_column_mappings(
            island_df, column_info
        )

    async def clean_credit_debit_columns(
        self, original_df: pd.DataFrame, mapped_columns: List, unmapped_attributes: List
    ) -> Tuple[Dict, List]:
        cb = {}
        if CREDIT in unmapped_attributes or DEBIT in unmapped_attributes:
            transaction_amount_item = next(
                item
                for item in mapped_columns
                if item["mapped_attribute"] == "transaction_amount"
            )

            amount_column_name = transaction_amount_item["name"]
            amount_column_region = transaction_amount_item["region"]

            cb = await clean_credit_debit(
                original_df,
                self.column_mapping_agent,
                amount_column_name,
                amount_column_region,
            )

            mapped_columns.remove(transaction_amount_item)
            unmapped_attributes = [
                attr for attr in unmapped_attributes if attr not in [CREDIT, DEBIT]
            ]
        return cb, unmapped_attributes

    async def detect_missing_attributes(
        self, original_df: pd.DataFrame, region: str, unmapped_attributes: List
    ) -> Tuple:
        return await self.missing_attributes_agent.detect_missing_attributes(
            original_df, region, unmapped_attributes
        )

    def generate_transformation_config(
        self,
        mapped_attributes: List[Dict[str, Any]],
        mapped_columns: List[Dict[str, Any]],
        cb: Any,
    ) -> Dict[str, Any]:
        """Generate a transformation configuration based on mapped attributes and columns."""
        try:
            # Construct the template_config
            template_config = {
                "actions": [
                    {
                        "type": "extract_columns",
                        "config": {"column_mappings": mapped_columns},
                    }
                ]
            }

            additional_attributes = []
            for attr in mapped_attributes:
                attribute = {
                    "name": attr["name"],
                    "value": attr["value"],
                    "region": attr["region"],
                    "attribute_type": attr["attribute_type"],
                }
                additional_attributes.append(attribute)

            # Only add the add_attributes action if additional_attributes is not empty
            if additional_attributes:
                template_config["actions"].append(
                    {
                        "type": "add_attributes",
                        "config": {"additional_attributes": additional_attributes},
                    }
                )

            if cb:
                template_config["actions"].insert(
                    0, {"type": "add_credit_debit", "config": {"config": cb}}
                )

            return template_config
        except Exception as e:
            logger.error(f"Error in generate_transformation_config: {str(e)}")
            return {}
