import structlog

from pantheon.ai_agents.agents.file_import_agent.activities.find_missing_attributes.helpers.fma_helper import (
    MissingAttributesAgent,
)
from pantheon.ai_agents.agents.file_import_agent.activities.find_missing_attributes.schema.fma_schema import (
    FindMissingAttributesInput,
    FindMissingAttributesOutput,
)

logger = structlog.get_logger(__name__)


async def find_missing_attributes_activity(
    input_data: FindMissingAttributesInput,
) -> FindMissingAttributesOutput:
    logger.info("Starting find_missing_attributes_activity")

    agent = MissingAttributesAgent()

    try:
        (
            mapped_attributes,
            search_still_unmapped,
            opening_balance,
        ) = await agent.detect_missing_attributes(
            input_data.original_df, input_data.region, input_data.unmapped_attributes
        )

        output = FindMissingAttributesOutput(
            mapped_attributes=mapped_attributes,
            search_still_unmapped=search_still_unmapped,
            opening_balance=opening_balance,
        )

        logger.info("find_missing_attributes_activity completed successfully")
        return output
    except Exception as e:
        logger.exception("Error in find_missing_attributes_activity", error=str(e))
        return None
