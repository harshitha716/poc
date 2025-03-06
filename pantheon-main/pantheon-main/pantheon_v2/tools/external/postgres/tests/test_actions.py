import pytest
from unittest.mock import AsyncMock, MagicMock

from pantheon_v2.tools.external.postgres.tool import PostgresTool
from pantheon_v2.tools.external.postgres.models import (
    QueryParams,
    BatchInsertParams,
    UpdateParams,
    QueryResult,
    ExecuteResult,
)


@pytest.fixture
def mock_tool():
    tool = PostgresTool({})
    tool.async_session = MagicMock()
    return tool


class TestPostgresActions:
    @pytest.mark.asyncio
    async def test_query_with_results(self, mock_tool):
        # Mock setup
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.returns_rows = True
        mock_result.keys.return_value = ["id", "name"]
        mock_result.fetchall.return_value = [(1, "test")]

        mock_session.__aenter__.return_value = mock_session
        mock_session.execute.return_value = mock_result
        mock_tool.async_session.return_value = mock_session

        # Execute query
        params = QueryParams(query="SELECT * FROM test", parameters={"param": "value"})
        result = await mock_tool.query(params)

        # Assertions
        # assert isinstance(result, QueryResult)
        assert result.columns == ["id", "name"]
        assert result.rows == [{"id": 1, "name": "test"}]
        assert result.row_count == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_no_results(self, mock_tool):
        # Mock setup
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.returns_rows = False

        mock_session.__aenter__.return_value = mock_session
        mock_session.execute.return_value = mock_result
        mock_tool.async_session.return_value = mock_session

        # Execute query
        params = QueryParams(query="SELECT * FROM empty")
        result = await mock_tool.query(params)

        # Assertions
        assert isinstance(result, QueryResult)
        assert result.columns == []
        assert result.rows == []
        assert result.row_count == 0

    async def test_insert_single_record(self, mock_tool):
        # Mock setup
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1

        mock_session.__aenter__.return_value = mock_session
        mock_session.execute.return_value = mock_result
        mock_session.begin.return_value = AsyncMock()
        mock_tool.async_session.return_value = mock_session

        # Execute insert
        params = BatchInsertParams(
            operations=[
                {"table": "test_table", "values": {"name": "test", "value": 123}}
            ]
        )
        result = await mock_tool.insert(params)

        # Assertions
        assert isinstance(result, ExecuteResult)
        assert result.success is True
        assert result.affected_rows == 1
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_multiple_records(self, mock_tool):
        # Mock setup
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1

        mock_transaction = AsyncMock()
        mock_transaction.__aenter__.return_value = mock_transaction

        mock_session.__aenter__.return_value = mock_session
        mock_session.begin.return_value = mock_transaction
        mock_session.execute.return_value = mock_result
        mock_tool.async_session.return_value = mock_session

        # Execute insert
        params = BatchInsertParams(
            operations=[
                {"table": "test_table", "values": {"name": "test1", "value": 123}},
                {"table": "test_table", "values": {"name": "test2", "value": 456}},
            ]
        )
        result = await mock_tool.insert(params)

        # Assertions
        assert isinstance(result, ExecuteResult)
        assert result.success is True
        assert result.affected_rows == 2
        assert mock_session.execute.call_count == 2
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update(self, mock_tool):
        # Mock setup
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1

        # Create a mock transaction context
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__.return_value = mock_transaction

        mock_session.__aenter__.return_value = mock_session
        mock_session.begin.return_value = mock_transaction
        mock_session.execute.return_value = mock_result
        mock_tool.async_session.return_value = mock_session

        # Execute update
        params = UpdateParams(
            table="test_table", values={"name": "updated"}, where={"id": 1}
        )
        result = await mock_tool.update(params)

        # Assertions
        assert isinstance(result, ExecuteResult)
        assert result.success is True
        assert result.affected_rows == 1
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.parametrize("action_method", ["query", "insert", "update"])
    @pytest.mark.asyncio
    async def test_error_handling(self, action_method, mock_tool):
        # Mock setup
        mock_session = AsyncMock()
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__.return_value = mock_transaction

        mock_session.__aenter__.return_value = mock_session
        mock_session.begin.return_value = mock_transaction
        mock_session.execute.side_effect = Exception("Database error")
        mock_tool.async_session.return_value = mock_session

        # Prepare parameters based on the action
        if action_method == "query":
            params = QueryParams(query="SELECT * FROM test")
        elif action_method == "insert":
            params = BatchInsertParams(
                operations=[{"table": "test", "values": {"name": "test"}}]
            )
        else:  # update
            params = UpdateParams(
                table="test", values={"name": "test"}, where={"id": 1}
            )

        # Execute and verify error handling
        with pytest.raises(Exception) as exc_info:
            await getattr(mock_tool, action_method)(params)
        assert str(exc_info.value) == "Database error"
