"""Tests for the promptfoo provider implementation."""

import pytest
from unittest.mock import patch, Mock, AsyncMock
import base64
from io import BytesIO

from pantheon_v2.core.evals.provider import (
    get_chain_config,
    extract_chain_id,
    process_file,
    fetch_files_from_gcs,
    create_prompt,
    build_chain_for_test,
    process_request,
    call_api,
)
from pantheon_v2.core.evals.models.models import ProviderResponse, TokenUsage
from pantheon_v2.core.modelrouter.models.models import ModelResponse, Usage
from pantheon_v2.core.modelrouter.constants.constants import SupportedLLMModels
from pantheon_v2.core.prompt.generic import GenericPrompt
from pantheon_v2.core.prompt.chain import PromptChain
from pantheon_v2.tools.external.gcs.models import DownloadFromGCSOutput


@pytest.fixture
def mock_model_response():
    return ModelResponse(
        content="test response",
        model=SupportedLLMModels.GPT_4,
        usage=Usage(total_tokens=10, prompt_tokens=5, completion_tokens=5),
        raw_response={},
        parsed_response={"response": "test response"},
    )


@pytest.fixture
def mock_gcs_tool():
    mock = Mock()
    mock.download_from_gcs = AsyncMock()
    return mock


@pytest.fixture
def test_chain_config():
    return {
        "id": "test_chain",
        "response_model": "pantheon_v2.core.evals.models.models.ProviderResponse",
        "prompts": [{"id": "test_prompt", "template": "test_template.txt"}],
    }


def test_get_chain_config():
    """Test extracting valid chain configuration."""
    config = {"chains": [{"id": "test", "data": "value"}]}
    result = get_chain_config(config, "test")
    assert result["data"] == "value"


def test_get_chain_config_not_found():
    """Test extracting missing chain configuration."""
    with pytest.raises(ValueError):
        get_chain_config({"chains": []}, "missing")


def test_extract_chain_id():
    """Test extracting chain ID from test configuration."""
    test_config = {"chain": "${chains.test_chain}"}
    assert extract_chain_id(test_config) == "test_chain"


@pytest.mark.asyncio
async def test_process_file(mock_gcs_tool):
    """Test processing a file with default prompt IDs."""
    file_content = b"test content"
    content_io = BytesIO(file_content)
    mock_gcs_tool.download_from_gcs.return_value = DownloadFromGCSOutput(
        content=content_io, bucket_name="test-bucket", file_name="test.txt"
    )

    result = await process_file(mock_gcs_tool, {"path": "/test.txt"})
    assert result["content"] == base64.b64encode(file_content).decode("utf-8")
    assert result["prompt_ids"] == "*"


@pytest.mark.asyncio
async def test_process_file_with_prompt_ids(mock_gcs_tool):
    """Test processing a file with specific prompt IDs."""
    file_content = b"test content"
    content_io = BytesIO(file_content)
    mock_gcs_tool.download_from_gcs.return_value = DownloadFromGCSOutput(
        content=content_io, bucket_name="test-bucket", file_name="test.txt"
    )

    result = await process_file(
        mock_gcs_tool, {"path": "/test.txt", "prompt_ids": ["id1", "id2"]}
    )
    assert result["prompt_ids"] == ["id1", "id2"]


@pytest.mark.asyncio
async def test_process_file_error(mock_gcs_tool):
    """Test error handling during file processing."""
    mock_gcs_tool.download_from_gcs.side_effect = Exception("Test error")
    with pytest.raises(Exception):
        await process_file(mock_gcs_tool, {"path": "/test.txt"})


@pytest.mark.asyncio
async def test_fetch_files_from_gcs(mock_gcs_tool):
    """Test fetching multiple files from GCS."""
    file_content = b"test content"
    content_io = BytesIO(file_content)
    mock_gcs_tool.download_from_gcs.return_value = DownloadFromGCSOutput(
        content=content_io, bucket_name="test-bucket", file_name="test.txt"
    )

    files = [{"path": "/test1.txt"}, {"path": "/test2.txt", "prompt_ids": ["id1"]}]

    results = await fetch_files_from_gcs(mock_gcs_tool, files)
    assert len(results) == 2
    assert all(isinstance(result, dict) for result in results)
    assert results[0]["prompt_ids"] == "*"
    assert results[1]["prompt_ids"] == ["id1"]


def test_create_prompt(tmp_path):
    """Test creating a prompt with valid template file."""
    template_file = tmp_path / "test_template.txt"
    template_file.write_text("Test template")

    prompt = create_prompt(template_file, {"var": "value"})
    assert isinstance(prompt, GenericPrompt)
    assert prompt.config.variables == {"var": "value"}


def test_create_prompt_missing_template(tmp_path):
    """Test creating a prompt with missing template file."""
    with pytest.raises(FileNotFoundError):
        create_prompt(tmp_path / "missing.txt", {})


@pytest.mark.asyncio
async def test_build_chain_for_test(mock_gcs_tool, test_chain_config, tmp_path):
    """Test building a chain with valid configuration."""
    template_file = tmp_path / "test_template.txt"
    template_file.write_text("Test template")
    test_chain_config["prompts"][0]["template"] = str(template_file)

    chain = await build_chain_for_test(
        test_chain_config, {"variables": {"test": "value"}}, mock_gcs_tool
    )
    assert isinstance(chain, PromptChain)


@pytest.mark.asyncio
async def test_build_chain_for_test_with_files(
    mock_gcs_tool, test_chain_config, tmp_path
):
    """Test building a chain with file attachments."""
    # Test that text files are not supported and raise appropriate error
    template_file = tmp_path / "test_template.txt"
    template_file.write_text("Test template")
    test_chain_config["prompts"][0]["template"] = str(template_file)

    file_content = b"test content"
    content_io = BytesIO(file_content)
    mock_gcs_tool.download_from_gcs.return_value = DownloadFromGCSOutput(
        content=content_io, bucket_name="test-bucket", file_name="test.txt"
    )

    with pytest.raises(
        ValueError,
        match="File type is text, not supported. Please use add_text instead.",
    ):
        await build_chain_for_test(
            test_chain_config,
            {"variables": {"test": "value"}, "files": ["/test.txt"]},
            mock_gcs_tool,
        )


@pytest.mark.asyncio
async def test_process_request(mock_model_response, test_chain_config, tmp_path):
    """Test processing a request with mocked router."""
    with patch(
        "pantheon_v2.core.evals.provider.ModelRouterFactory"
    ) as mock_factory, patch(
        "pantheon_v2.core.evals.provider.GCSTool"
    ) as mock_gcs_class:
        # Mock GCS tool to avoid auth issues
        mock_gcs = Mock()
        mock_gcs.initialize = AsyncMock()
        mock_gcs_class.return_value = mock_gcs

        # Mock router
        mock_router = Mock()
        mock_router.generate = AsyncMock(return_value=mock_model_response)
        mock_factory.get_router.return_value = mock_router

        template_file = tmp_path / "test_template.txt"
        template_file.write_text("Test template")
        test_chain_config["prompts"][0]["template"] = str(template_file)

        response = await process_request(
            test_chain_config, {"variables": {"test": "value"}}, "gpt-4", "test-project"
        )
        assert isinstance(response, ModelResponse)
        assert response.content == "test response"


@pytest.mark.asyncio
async def test_process_request_error(mock_model_response, test_chain_config, tmp_path):
    """Test error handling in request processing."""
    with patch(
        "pantheon_v2.core.evals.provider.ModelRouterFactory"
    ) as mock_factory, patch(
        "pantheon_v2.core.evals.provider.GCSTool"
    ) as mock_gcs_class:
        # Mock GCS tool to avoid auth issues
        mock_gcs = Mock()
        mock_gcs.initialize = AsyncMock()
        mock_gcs_class.return_value = mock_gcs

        # Mock router to raise error
        mock_router = Mock()
        mock_router.generate = AsyncMock(side_effect=Exception("Router error"))
        mock_factory.get_router.return_value = mock_router

        template_file = tmp_path / "test_template.txt"
        template_file.write_text("Test template")
        test_chain_config["prompts"][0]["template"] = str(template_file)

        with pytest.raises(Exception, match="Router error"):
            await process_request(
                test_chain_config,
                {"variables": {"test": "value"}},
                "gpt-4",
                "test-project",
            )


def test_create_provider_response(mock_model_response):
    """Test creating a standardized provider response."""
    response = ProviderResponse(
        output=mock_model_response.parsed_response,
        token_usage=TokenUsage(
            total=mock_model_response.usage.total_tokens,
            prompt=mock_model_response.usage.prompt_tokens,
            completion=mock_model_response.usage.completion_tokens,
        ),
    ).model_dump()
    assert "output" in response
    assert "token_usage" in response
    assert response["token_usage"]["total"] == 10
    assert response["token_usage"]["prompt"] == 5
    assert response["token_usage"]["completion"] == 5
    assert response["output"] == mock_model_response.parsed_response


def test_call_api(mock_model_response, test_chain_config, tmp_path):
    """Test the main API interface function."""
    with patch(
        "pantheon_v2.core.evals.provider.process_request"
    ) as mock_process, patch(
        "pantheon_v2.core.evals.provider.create_provider_response"
    ) as mock_create_response:
        mock_process.return_value = mock_model_response
        mock_create_response.return_value = {
            "output": {"response": "test response"},
            "token_usage": {"total": 10, "prompt": 5, "completion": 5},
        }

        template_file = tmp_path / "test_template.txt"
        template_file.write_text("Test template")
        test_chain_config["prompts"][0]["template"] = str(template_file)

        result = call_api(
            "test prompt",
            {"config": {"model_name": "gpt-4", "chains": [test_chain_config]}},
            {"test": {"chain": "${chains.test_chain}"}, "vars": {}},
        )
        assert isinstance(result, dict)
        assert "output" in result
        assert "token_usage" in result
        assert result["output"] == {"response": "test response"}
        assert result["token_usage"]["total"] == 10


def test_call_api_error():
    """Test error handling in the API interface."""
    with patch("pantheon_v2.core.evals.provider.process_request") as mock_process:
        mock_process.side_effect = Exception("API error")

        result = call_api(
            "test prompt",
            {"config": {"model_name": "gpt-4", "chains": [{"id": "test_chain"}]}},
            {"test": {"chain": "${chains.test_chain}"}, "vars": {}},
        )
        assert isinstance(result, dict)
        assert "error" in result
        assert "API error" in result["error"]
