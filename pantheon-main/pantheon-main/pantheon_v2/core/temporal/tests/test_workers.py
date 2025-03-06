import pytest
from unittest.mock import AsyncMock, patch

from pantheon_v2.core.temporal.workers import TemporalWorkerManager
from zamp_public_workflow_sdk.temporal.temporal_worker import TemporalWorkerConfig


@pytest.fixture
def mock_settings():
    with patch("pantheon_v2.core.temporal.workers.Settings") as mock_settings:
        mock_settings.TEMPORAL_HOST = "test.host"
        mock_settings.TEMPORAL_NAMESPACE = "test-namespace"
        mock_settings.is_cloud.return_value = True
        mock_settings.get_temporal_certs.return_value = ("cert", "key")
        mock_settings.TEMPORAL_LARGE_PAYLOAD_BUCKET = "test-bucket"
        mock_settings.GCP_PROJECT_ID = "test-project"
        yield mock_settings


@pytest.fixture
def worker_manager(mock_settings):
    with patch("google.cloud.storage.Client") as mock_storage_client:
        mock_storage_client.return_value.get_bucket.return_value.blob.return_value = (
            None
        )
        return TemporalWorkerManager()


@pytest.mark.asyncio
async def test_worker_manager_init(worker_manager):
    """Test that TemporalWorkerManager initializes with correct configuration."""
    assert worker_manager.client_config.host == "test.host"
    assert worker_manager.client_config.namespace == "test-namespace"
    assert worker_manager.client_config.is_cloud is True
    assert worker_manager.client_config.client_cert == "cert"
    assert worker_manager.client_config.client_key == "key"


@pytest.mark.asyncio
async def test_worker_manager_start_success(worker_manager):
    """Test successful worker start."""
    mock_service = AsyncMock()
    mock_worker = AsyncMock()
    mock_service.worker.return_value = mock_worker

    with patch(
        "zamp_public_workflow_sdk.temporal.temporal_service.TemporalService.connect",
        return_value=mock_service,
    ) as mock_connect:
        await worker_manager.start()

        # Verify service connection was attempted
        mock_connect.assert_called_once_with(worker_manager.client_config)

        # Verify worker was created with correct config
        mock_service.worker.assert_called_once()
        worker_config = mock_service.worker.call_args[0][0]
        assert isinstance(worker_config, TemporalWorkerConfig)
        assert worker_config.task_queue == worker_manager.task_queue

        # Verify worker was started
        mock_worker.run.assert_called_once()


@pytest.mark.asyncio
async def test_worker_manager_start_failure(worker_manager):
    """Test worker start failure."""
    with patch(
        "zamp_public_workflow_sdk.temporal.temporal_service.TemporalService.connect",
        side_effect=Exception("Connection failed"),
    ):
        with pytest.raises(Exception) as exc_info:
            await worker_manager.start()
        assert str(exc_info.value) == "Connection failed"


@pytest.mark.asyncio
async def test_run_worker():
    """Test the run_worker helper function."""
    mock_manager = AsyncMock()
    with patch(
        "pantheon_v2.core.temporal.workers.TemporalWorkerManager",
        return_value=mock_manager,
    ):
        from pantheon_v2.core.temporal.workers import run_worker

        await run_worker()
        mock_manager.start.assert_called_once()
