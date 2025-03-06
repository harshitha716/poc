"""Provider implementation for promptfoo evaluation framework with enhanced capabilities."""

from typing import Dict, Any, Union, List
import asyncio
from dotenv import load_dotenv
import os

from pantheon_v2.core.evals.models.models import ProviderResponse, TokenUsage
from pantheon_v2.core.modelrouter.factory import ModelRouterFactory
from pantheon_v2.core.modelrouter.models.models import GenerationRequest, ModelResponse
from pantheon_v2.core.common.models import MessageRole
from pantheon_v2.core.modelrouter.constants.constants import (
    SupportedLLMModels,
    RouterProvider,
)
from pantheon_v2.core.prompt.models import PromptConfig
from pantheon_v2.core.prompt.generic import GenericPrompt
from pantheon_v2.core.prompt.chain import PromptChain
from pantheon_v2.settings.settings import Settings
from pantheon_v2.tools.external.gcs.tool import GCSTool
from pantheon_v2.tools.external.gcs.models import (
    DownloadFromGCSInput,
    DownloadFromGCSOutput,
)
from pantheon_v2.core.evals.constants import ZAMP_EVALS_BUCKET_NAME
import base64
from pantheon_v2.utils.type_utils import get_reference_from_fqn
from pantheon_v2.core.prompt.chain import ChainConfig

import structlog

logger = structlog.get_logger(__name__)


def get_chain_config(provider_config: Dict[str, Any], chain_id: str) -> Dict[str, Any]:
    """Extract and validate chain configuration."""
    chains = provider_config.get("chains", [])
    chain_config = next((chain for chain in chains if chain["id"] == chain_id), None)

    if not chain_config:
        raise ValueError(f"Chain configuration not found for id: {chain_id}")

    return chain_config


def extract_chain_id(test_config: Dict[str, Any]) -> str:
    """Extract chain ID from test configuration."""
    chain_ref = test_config.get("chain", "")
    return chain_ref.replace("${chains.", "").replace("}", "")


async def process_file(gcs_tool: GCSTool, file_info: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single file from GCS."""
    try:
        params = DownloadFromGCSInput(
            bucket_name=ZAMP_EVALS_BUCKET_NAME, file_name=file_info["path"].lstrip("/")
        )
        content: DownloadFromGCSOutput = await gcs_tool.download_from_gcs(params)
        content_base64 = base64.b64encode(content.content.read()).decode("utf-8")
        print("fetched file", file_info["path"])
        return {
            "content": content_base64,
            "prompt_ids": file_info.get("prompt_ids", "*"),
        }
    except Exception as e:
        logger.error(f"Failed to process file {file_info['path']}: {str(e)}")
        raise


async def fetch_files_from_gcs(
    gcs_tool: GCSTool, files: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Fetch and process multiple files from GCS."""
    return [await process_file(gcs_tool, file_info) for file_info in files]


def create_prompt(template_path, variables: Dict[str, Any]) -> GenericPrompt:
    """Create a prompt with given template and variables."""
    if template_path == "":
        raise FileNotFoundError(f"Template file not found: {template_path}")

    # Convert Path object to string if needed
    template_path_str = str(template_path)

    # Check if file exists before creating the prompt
    if template_path_str.endswith(".txt") and not os.path.exists(template_path_str):
        raise FileNotFoundError(f"Template file not found: {template_path_str}")

    return GenericPrompt(
        config=PromptConfig(
            template=template_path_str, variables=variables, role=MessageRole.USER
        )
    )


async def build_chain_for_test(
    chain_config: Dict[str, Any], test_vars: Dict[str, Any], gcs_tool: GCSTool
) -> PromptChain:
    """Build a prompt chain for a specific test case."""
    response_model = get_reference_from_fqn(chain_config["response_model"])
    chain = PromptChain(config=ChainConfig(response_model=response_model))

    # Process files if they exist
    files = test_vars.get("files", [])
    print("files", files)
    if files:
        file_configs = [
            {"path": f, "prompt_ids": "*"} if isinstance(f, str) else f for f in files
        ]
        print("Fetching files from GCS since files are passed in config")
        processed_files = await fetch_files_from_gcs(gcs_tool, file_configs)
    else:
        processed_files = []

    # Add prompts to chain
    for prompt_config in chain_config["prompts"]:
        prompt_id = prompt_config["id"]
        template_path = prompt_config["template"]

        prompt = create_prompt(
            template_path=template_path, variables=test_vars.get("variables", {})
        )

        # Add relevant files to prompt
        for file_info in processed_files:
            prompt_ids = file_info["prompt_ids"]
            if prompt_ids == "*" or prompt_id in prompt_ids:
                prompt.add_file(base64_content=file_info["content"])

        chain.add_prompt(prompt)

    return chain


async def process_request(
    chain_config: Dict[str, Any],
    test_vars: Dict[str, Any],
    model_name: str,
    project_id: str,
) -> ModelResponse:
    """Process a single evaluation request."""
    gcs_tool = GCSTool(config={"project_id": project_id})
    await gcs_tool.initialize()

    chain = await build_chain_for_test(
        chain_config=chain_config, test_vars=test_vars, gcs_tool=gcs_tool
    )

    request = GenerationRequest(
        prompt_chain=chain,
        model_name=SupportedLLMModels(model_name),
    )

    return await ModelRouterFactory.get_router(RouterProvider.LITELLM).generate(request)


def create_provider_response(response: ModelResponse) -> Dict[str, Any]:
    """Create standardized provider response."""
    return ProviderResponse(
        output=response.parsed_response.model_dump(),
        token_usage=TokenUsage(
            total=response.usage.total_tokens,
            prompt=response.usage.prompt_tokens,
            completion=response.usage.completion_tokens,
        ),
    ).model_dump()


def call_api(
    prompt: Union[str, Dict[str, Any]], options: Dict[str, Any], context: Dict[str, Any]
) -> Dict[str, Any]:
    """Promptfoo provider interface function."""
    try:
        load_dotenv()

        provider_config = options.get("config", {})
        chain_id = extract_chain_id(context.get("test", {}))
        chain_config = get_chain_config(provider_config, chain_id)

        # Get or create event loop instead of asyncio.run
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            process_request(
                chain_config=chain_config,
                test_vars=context.get("vars", {}),
                model_name=provider_config["model_name"],
                project_id=Settings.GCP_PROJECT_ID,
            )
        )
        # Give event loop a chance to process background tasks
        print("Sleeping for 20 seconds after response to allow langfuse to process")
        loop.run_until_complete(asyncio.sleep(20))

        provider_response = create_provider_response(response)

        return provider_response

    except Exception as e:
        logger.error(f"Error in provider: {str(e)}")
        return ProviderResponse(error=str(e)).model_dump()
