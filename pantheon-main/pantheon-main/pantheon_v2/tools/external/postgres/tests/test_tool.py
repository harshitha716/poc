import pytest
from unittest.mock import MagicMock, patch

from pantheon_v2.tools.external.postgres.tool import PostgresTool


@pytest.fixture
def postgres_config():
    return {
        "host": "localhost",
        "port": "5432",
        "database": "test_db",
        "username": "test_user",
        "password": "test_password",
        "pool_size": 5,
        "max_overflow": 10,
    }


@pytest.fixture
def postgres_tool(postgres_config):
    return PostgresTool(config=postgres_config)


class TestPostgresTool:
    @pytest.mark.asyncio
    async def test_initialize_success(self, postgres_tool):
        """Test successful initialization of PostgresTool"""
        with patch(
            "pantheon_v2.tools.external.postgres.tool.create_async_engine"
        ) as mock_engine:
            mock_engine.return_value = MagicMock()

            await postgres_tool.initialize()

            # Verify engine creation
            mock_engine.assert_called_once()
            assert postgres_tool.engine is not None
            assert postgres_tool.async_session is not None

    @pytest.mark.asyncio
    async def test_initialize_failure(self, postgres_tool):
        """Test initialization failure of PostgresTool"""
        with patch(
            "pantheon_v2.tools.external.postgres.tool.create_async_engine",
            side_effect=Exception("Database Error"),
        ):
            with pytest.raises(Exception) as exc_info:
                await postgres_tool.initialize()

            assert str(exc_info.value) == "Database Error"
