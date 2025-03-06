from unittest.mock import patch

from pantheon_v2.utils.trace_utils import (
    get_trace_id,
    TRACE_ID_CONTEXT_KEY,
    TRACE_ID_HEADER_KEY,
)


class TestTraceUtils:
    @patch("structlog.contextvars.get_contextvars")
    def test_get_trace_id_exists(self, mock_get_contextvars):
        # Setup
        expected_trace_id = "test-trace-id"
        mock_get_contextvars.return_value = {TRACE_ID_CONTEXT_KEY: expected_trace_id}

        # Exercise
        result = get_trace_id()

        # Verify
        assert result == expected_trace_id
        mock_get_contextvars.assert_called_once()

    @patch("structlog.contextvars.get_contextvars")
    def test_get_trace_id_not_exists(self, mock_get_contextvars):
        # Setup
        mock_get_contextvars.return_value = {}

        # Exercise
        result = get_trace_id()

        # Verify
        assert result is None
        mock_get_contextvars.assert_called_once()

    @patch("structlog.contextvars.get_contextvars")
    def test_get_trace_id_with_other_context_vars(self, mock_get_contextvars):
        # Setup
        expected_trace_id = "test-trace-id"
        mock_get_contextvars.return_value = {
            TRACE_ID_CONTEXT_KEY: expected_trace_id,
            "other_key": "other_value",
        }

        # Exercise
        result = get_trace_id()

        # Verify
        assert result == expected_trace_id
        mock_get_contextvars.assert_called_once()

    @patch("structlog.contextvars.get_contextvars")
    def test_get_trace_id_with_none_value(self, mock_get_contextvars):
        # Setup
        mock_get_contextvars.return_value = {TRACE_ID_CONTEXT_KEY: None}

        # Exercise
        result = get_trace_id()

        # Verify
        assert result is None
        mock_get_contextvars.assert_called_once()

    def test_constants(self):
        # Verify constants are defined correctly
        assert TRACE_ID_CONTEXT_KEY == "pantheon_trace_id"
        assert TRACE_ID_HEADER_KEY == "pantheon-trace-id"
