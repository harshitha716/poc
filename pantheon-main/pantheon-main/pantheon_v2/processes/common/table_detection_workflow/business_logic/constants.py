from pantheon_v2.core.modelrouter.constants.constants import (
    SupportedLLMModels,
    RouterProvider,
)
from enum import Enum

# Default values for column mapping
DEFAULT_SAMPLE_ROWS = 3
DEFAULT_TEMPERATURE = 0.1  # Low temperature for consistent mappings

# Model configuration
DEFAULT_MODEL = SupportedLLMModels.CLAUDE_3_7
DEFAULT_ROUTER_PROVIDER = RouterProvider.LITELLM


# Metadata extraction modes
class MetadataMode(str, Enum):
    ALL = "all"  # Extract all possible key-value pairs
    TARGETED = "targeted"  # Extract only specified target attributes


# Template names for metadata extraction
METADATA_TEMPLATE_TARGETED = "extract_metadata_targeted.txt"
METADATA_TEMPLATE_ALL = "extract_metadata.txt"
