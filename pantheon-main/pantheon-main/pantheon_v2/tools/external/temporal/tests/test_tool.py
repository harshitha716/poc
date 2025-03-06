import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from temporalio.common import RetryPolicy
from datetime import timedelta
import uuid

from pantheon_v2.tools.external.temporal.tool import TemporalTool
from pantheon_v2.tools.external.temporal.models import (
    WorkflowParams,
    WorkflowResponse,
)
from zamp_public_workflow_sdk.temporal.models.temporal_models import RunWorkflowParams


@pytest.fixture
def temporal_config():
    return {
        "host": "test-host:7233",
        "namespace": "test-namespace",
        "is_cloud": True,
        "client_cert": "test-cert",
        "client_key": "test-key",
    }


@pytest.fixture
def workflow_params():
    return WorkflowParams(
        workflow="TestWorkflow",
        arg={"test": "data"},
        task_queue="test-queue",
        id=str(uuid.uuid4()),
        retry_policy=RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_attempts=3,
            maximum_interval=timedelta(seconds=10),
            non_retryable_error_types=["TestError"],
        ),
    )


@pytest.fixture
async def temporal_tool(temporal_config):
    tool = TemporalTool(temporal_config)
    return tool


@pytest.mark.asyncio
async def test_get_api_handle_success(temporal_tool, temporal_config):
    """Test successful API handle retrieval"""
    with patch(
        "zamp_public_workflow_sdk.temporal.temporal_service.TemporalService.connect",
        new_callable=AsyncMock,
    ) as mock_connect:
        mock_client = MagicMock()
        mock_connect.return_value = mock_client

        result = await TemporalTool.get_api_handle(temporal_tool)

        mock_connect.assert_called_once()
        assert result == mock_client


@pytest.mark.asyncio
async def test_get_api_handle_failure(temporal_tool):
    """Test API handle retrieval failure"""
    with patch(
        "zamp_public_workflow_sdk.temporal.temporal_service.TemporalService.connect",
        new_callable=AsyncMock,
    ) as mock_connect:
        mock_connect.side_effect = Exception("Connection failed")

        with pytest.raises(Exception) as exc_info:
            await TemporalTool.get_api_handle(temporal_tool)

        assert str(exc_info.value) == "Connection failed"


@pytest.mark.asyncio
async def test_invoke_workflow_success(temporal_tool, workflow_params):
    """Test successful workflow invocation"""
    mock_api = MagicMock()
    mock_result = MagicMock()
    mock_result.run_id = "test-run-id"
    mock_api.start_async_workflow = AsyncMock(return_value=mock_result)

    with patch.object(
        TemporalTool, "get_api_handle", new_callable=AsyncMock
    ) as mock_get_api:
        mock_get_api.return_value = mock_api

        result = await temporal_tool.invoke_workflow(workflow_params)

        assert isinstance(result, WorkflowResponse)
        assert result.workflow_id == workflow_params.id
        assert result.run_id == "test-run-id"
        assert result.result == mock_result

        mock_api.start_async_workflow.assert_called_once()
        call_args = mock_api.start_async_workflow.call_args[0][0]
        assert isinstance(call_args, RunWorkflowParams)
        assert call_args.workflow == workflow_params.workflow
        assert call_args.arg == workflow_params.arg
        assert call_args.task_queue == workflow_params.task_queue
        assert call_args.id == workflow_params.id
        assert call_args.retry_policy == workflow_params.retry_policy


@pytest.mark.asyncio
async def test_invoke_workflow_failure(temporal_tool, workflow_params):
    """Test workflow invocation failure"""
    with patch.object(
        TemporalTool, "get_api_handle", new_callable=AsyncMock
    ) as mock_get_api:
        mock_get_api.side_effect = Exception("Workflow failed")

        with pytest.raises(Exception) as exc_info:
            await temporal_tool.invoke_workflow(workflow_params)

        assert str(exc_info.value) == "Workflow failed"


@pytest.mark.asyncio
async def test_invoke_workflow_api_failure(temporal_tool, workflow_params):
    """Test workflow invocation with API failure"""
    mock_api = MagicMock()
    mock_api.start_async_workflow = AsyncMock(side_effect=Exception("API failed"))

    with patch.object(
        TemporalTool, "get_api_handle", new_callable=AsyncMock
    ) as mock_get_api:
        mock_get_api.return_value = mock_api

        with pytest.raises(Exception) as exc_info:
            await temporal_tool.invoke_workflow(workflow_params)

        assert str(exc_info.value) == "API failed"


@pytest.mark.asyncio
async def test_initialize_with_missing_config(temporal_config):
    """Test initialization with missing required config"""
    del temporal_config["host"]
    tool = TemporalTool(temporal_config)

    with pytest.raises(Exception):
        await TemporalTool.get_api_handle(tool)
