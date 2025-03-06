from typing import Dict, Any, List

import structlog

logger = structlog.get_logger(__name__)


def generate_transformation_config(
    mapped_attributes: List[Dict[str, Any]],
    mapped_columns: List[Dict[str, Any]],
    cb: Any,
) -> Dict[str, Any]:
    """
    Generate a transformation configuration based on mapped attributes and columns.

    Args:
        mapped_attributes (List[Dict[str, Any]]): List of mapped attributes
        mapped_columns (List[Dict[str, Any]]): List of mapped columns
        cb (Any): Credit/Debit configuration

    Returns:
        Dict[str, Any]: Transformation configuration
    """
    try:
        # Construct the base template_config with extract_columns action
        template_config = {
            "actions": [
                {
                    "type": "extract_columns",
                    "config": {"column_mappings": mapped_columns},
                }
            ]
        }

        # Process additional attributes
        additional_attributes = [
            {
                "name": attr["name"],
                "value": attr["value"],
                "region": attr["region"],
                "attribute_type": attr["attribute_type"],
            }
            for attr in mapped_attributes
        ]

        # Add add_attributes action if additional_attributes exist
        if additional_attributes:
            template_config["actions"].append(
                {
                    "type": "add_attributes",
                    "config": {"additional_attributes": additional_attributes},
                }
            )

        # Insert add_credit_debit action if cb is provided
        if cb:
            template_config["actions"].insert(
                0, {"type": "add_credit_debit", "config": {"config": cb}}
            )

        return template_config
    except Exception as e:
        logger.error(f"Error in generate_transformation_config: {str(e)}")
        return {}
