import logging
from typing import List, Optional, Dict, Any
import re
from pantheon.ai_agents.agents.file_import_agent.workflows.schema.fia_schema import (
    AddCreditDebitConfig,
    ColumnInfo,
    ColumnMapping,
    Action,
    ConfigResponse,
)

logger = logging.getLogger(__name__)


def extract_config(actions: List[Action], action_type: str) -> Optional[Dict]:
    try:
        for action in actions:
            if action.type == action_type:
                return action.config.get("config", action.config)
    except Exception as e:
        logger.error(f"Error extracting config: {str(e)}")
    return None


def destruct(
    config: dict,
) -> tuple[
    Optional[AddCreditDebitConfig],
    Optional[List[ColumnMapping]],
    Optional[List[str]],
    Optional[List[str]],
]:
    try:
        response = ConfigResponse(**config)

        add_credit_debit_config = extract_config(
            response.transformation_config.actions, "add_credit_debit"
        )
        extract_columns_config = extract_config(
            response.transformation_config.actions, "extract_columns"
        )

        return (
            AddCreditDebitConfig(**add_credit_debit_config)
            if add_credit_debit_config
            else None,
            [
                ColumnMapping(**mapping)
                for mapping in extract_columns_config.get("column_mappings", [])
            ]
            if extract_columns_config
            else None,
            response.unmapped_columns,
            response.errors,
        )
    except Exception as e:
        logger.error(f"Error processing config: {str(e)}")
        return None, None, None, None


def combine_column_info_and_mappings(
    column_info: List[ColumnInfo], column_mappings_template: List[ColumnMapping]
) -> List[Dict[str, Any]]:
    try:
        # Create a dictionary from column_info for easy lookup
        column_info_dict = {info.name: info.model_dump() for info in column_info}

        combined_mappings = []

        for mapping in column_mappings_template:
            try:
                name = mapping.name
                if name in column_info_dict:
                    # Combine the information from both sources
                    combined_mapping = {
                        **column_info_dict[name],  # Add all fields from column_info
                        **mapping.model_dump(),  # Add fields from column_mappings_template
                    }
                    combined_mappings.append(combined_mapping)
                else:
                    # If there's no matching column_info, use the mapping as is
                    combined_mappings.append(mapping.model_dump())
            except Exception as e:
                logger.error(f"Error processing mapping: {mapping}. Error: {str(e)}")

        return combined_mappings
    except Exception as e:
        logger.error(
            f"Error in combine_column_info_and_mappings: {str(e)} {column_info} {column_mappings_template}"
        )
        return []  # Return an empty list in case of error


def split_excel_ref(ref):
    return "".join(filter(str.isalpha, ref)), "".join(filter(str.isdigit, ref))


def update_region(original_region: str, new_start: int, new_end: int) -> str:
    column_part = re.match(r"([A-Z]+)", original_region).group(1)
    return f"{column_part}{new_start}:{column_part}{new_end}"
