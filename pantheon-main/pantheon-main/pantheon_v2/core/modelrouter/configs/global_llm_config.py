from typing import Dict
from pantheon_v2.core.modelrouter.constants.constants import SupportedLLMModels
from pantheon_v2.core.modelrouter.models.models import (
    ModelCapabilities,
    GlobalModelConfig,
)


class SUPPORTED_MODELS:
    """Global model configurations"""

    @classmethod
    def get_config(cls) -> Dict[SupportedLLMModels, GlobalModelConfig]:
        return {
            SupportedLLMModels.GPT_4O: GlobalModelConfig(
                capabilities=ModelCapabilities(
                    max_tokens=4096,
                    context_length=8192,
                    supports_functions=True,
                ),
                description="GPT-4 Turbo model with function calling support",
            ),
            SupportedLLMModels.GPT_4O_MINI: GlobalModelConfig(
                capabilities=ModelCapabilities(
                    max_tokens=4096,
                    context_length=128000,
                    supports_functions=True,
                ),
                description="GPT-4o-mini model with optimized performance",
            ),
            SupportedLLMModels.CLAUDE_3_5: GlobalModelConfig(
                capabilities=ModelCapabilities(
                    max_tokens=4096,
                    context_length=200000,
                    supports_functions=False,
                ),
                description="Claude 3.5 Sonnet model from Anthropic",
            ),
            SupportedLLMModels.CLAUDE_3_7: GlobalModelConfig(
                capabilities=ModelCapabilities(
                    max_tokens=4096,
                    context_length=200000,
                    supports_functions=False,
                ),
                description="Claude 3.7 Sonnet model from Anthropic",
            ),
            SupportedLLMModels.GPT_4: GlobalModelConfig(
                capabilities=ModelCapabilities(
                    max_tokens=8192,
                    context_length=8192,
                    supports_functions=True,
                ),
                description="Standard GPT-4 model with function calling support",
            ),
            SupportedLLMModels.GEMINI_FLASH_2: GlobalModelConfig(
                capabilities=ModelCapabilities(
                    max_tokens=8192,
                    context_length=1048576,
                    supports_functions=False,
                ),
                description="Gemini Flash 2 model",
            ),
            SupportedLLMModels.BEDROCK_CLAUDE_3_5: GlobalModelConfig(
                capabilities=ModelCapabilities(
                    max_tokens=4096,
                    context_length=200000,
                    supports_functions=False,
                ),
                description="Bedrock Claude 3.5 Sonnet model",
            ),
            SupportedLLMModels.GPT_O1: GlobalModelConfig(
                capabilities=ModelCapabilities(
                    max_tokens=20000,
                    context_length=200000,
                    supports_functions=False,
                ),
                description="GPT-O1 model",
            ),
            SupportedLLMModels.GPT_O3_MINI: GlobalModelConfig(
                capabilities=ModelCapabilities(
                    context_length=200000,
                    supports_functions=False,
                ),
                description="GPT-O3 Mini model",
            ),
        }
