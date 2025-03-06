from pantheon.ai_agents.tools.detect_island_and_clean.tool import (
    detect_largest_island,
    clean_dataframe,
)
from .schema.dic_schema import DetectIslandAndCleanInput, DetectIslandAndCleanOutput


def detect_island_and_clean(
    input_data: DetectIslandAndCleanInput,
) -> DetectIslandAndCleanOutput:
    region, island_df = detect_largest_island(input_data.df, input_data.start_row)
    island_df, region = clean_dataframe(island_df, region, 0.1)
    return DetectIslandAndCleanOutput(region=region, island_df=island_df)
