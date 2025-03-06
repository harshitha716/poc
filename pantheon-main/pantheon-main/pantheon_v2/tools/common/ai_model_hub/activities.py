from pantheon_v2.tools.common.ai_model_hub.tool import AIModelHubTool
from pantheon_v2.tools.common.ai_model_hub.models import (
    AIModelHubToolGenerateLLMInput,
    AIModelHubToolGenerateLLMOutput,
    AIModelHubToolGenerateEmbeddingsInput,
    AIModelHubToolGenerateEmbeddingsOutput,
)
from pantheon_v2.tools.core.activity_registry import ActivityRegistry


@ActivityRegistry.register_activity("Call LLM models to reason and generate a response")
async def generate_llm_model_response(
    params: AIModelHubToolGenerateLLMInput,
) -> AIModelHubToolGenerateLLMOutput:
    tool = AIModelHubTool()
    await tool.initialize()
    return await tool.generate(params)


@ActivityRegistry.register_activity("Generate embeddings from text or images")
async def generate_embeddings(
    params: AIModelHubToolGenerateEmbeddingsInput,
) -> AIModelHubToolGenerateEmbeddingsOutput:
    tool = AIModelHubTool()
    await tool.initialize()
    return await tool.generate_embeddings(params)
