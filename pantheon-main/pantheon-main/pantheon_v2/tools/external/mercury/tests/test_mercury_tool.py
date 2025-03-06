import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from pantheon_v2.tools.external.mercury.tool import MercuryTool
from pantheon_v2.tools.external.mercury.models import (
    Transaction,
    CreateTransactionRequest,
    GetTransactionParams,
    TransactionDetails,
)
from pantheon_v2.utils.api_client import HttpMethod


@pytest.fixture
def mock_config():
    return {"api_key": "test_api_key"}


@pytest.fixture
def mock_transaction():
    return Transaction(
        id="tx_123",
        feeId="fee_123",
        amount=1000.0,
        createdAt=datetime.now(),
        postedAt=datetime.now(),
        estimatedDeliveryDate=datetime.now(),
        status="pending",
        note="Test transaction",
        bankDescription="Bank transfer",
        externalMemo="External memo",
        counterpartyId="cp_123",
        details=TransactionDetails(),
        reasonForFailure=None,
        failedAt=None,
        dashboardLink="https://dashboard.mercury.com/tx/123",
        counterpartyName="Test Counterparty",
        counterpartyNickname="Test",
        kind="payment",
        currencyExchangeInfo=None,
        compliantWithReceiptPolicy=True,
        hasGeneratedReceipt=False,
        creditAccountPeriodId=None,
        mercuryCategory=None,
        generalLedgerCodeName=None,
        attachments=[],
        relatedTransactions=[],
    )


@pytest.fixture
async def mercury_tool(mock_config):
    tool = MercuryTool(mock_config)
    await tool.initialize()
    return tool


class TestMercuryTool:
    async def test_initialize(self, mock_config):
        tool = MercuryTool(mock_config)
        await tool.initialize()

        assert tool.config.api_key == "test_api_key"
        assert tool.client is not None
        assert "Authorization" in tool.client.default_headers
        assert tool.client.default_headers["Authorization"] == "Bearer test_api_key"

    async def test_initialize_failure(self):
        with pytest.raises(Exception):
            tool = MercuryTool({})  # Empty config should fail
            await tool.initialize()

    async def test_create_transaction(self, mercury_tool, mock_transaction):
        mercury_tool.client.request = AsyncMock(return_value=mock_transaction)

        request = CreateTransactionRequest(
            account_id="acc_123",
            recipient_id="rec_456",
            amount=1000.0,
            payment_method="domesticWire",
            idempotency_key="idem_123",
        )

        result = await mercury_tool.create_transaction(request)

        assert isinstance(result, Transaction)
        assert result.id == mock_transaction.id

        # Get the actual call arguments
        call_args = mercury_tool.client.request.call_args
        actual_data = call_args.kwargs["data"]

        # Check that all fields except amount match exactly
        assert actual_data["recipientId"] == "rec_456"
        assert actual_data["paymentMethod"] == "domesticWire"
        assert actual_data["idempotencyKey"] == "idem_123"

        # Verify amount is within the expected range (base amount + 0-0.99)
        assert 1000.0 <= actual_data["amount"] < 1001.0

        # Verify the other call parameters
        assert call_args.kwargs["method"] == HttpMethod.POST
        assert call_args.kwargs["endpoint"] == "/account/acc_123/transactions"
        assert call_args.kwargs["response_model"] == Transaction

    async def test_create_transaction_failure(self, mercury_tool):
        mercury_tool.client.request = AsyncMock(side_effect=Exception("API Error"))

        request = CreateTransactionRequest(
            account_id="acc_123",
            recipient_id="rec_456",
            amount=1000.0,
            payment_method="domesticWire",
            idempotency_key="idem_123",
        )

        with pytest.raises(Exception) as exc_info:
            await mercury_tool.create_transaction(request)
        assert str(exc_info.value) == "API Error"

    async def test_get_transaction(self, mercury_tool, mock_transaction):
        mercury_tool.client.request = AsyncMock(return_value=mock_transaction)

        params = GetTransactionParams(account_id="acc_123", transaction_id="tx_123")

        result = await mercury_tool.get_transaction(params)

        assert isinstance(result, Transaction)
        assert result.id == mock_transaction.id
        assert result.amount == mock_transaction.amount

        mercury_tool.client.request.assert_called_once_with(
            method=HttpMethod.GET,
            endpoint="/account/acc_123/transaction/tx_123",
            response_model=Transaction,
        )

    async def test_get_transaction_failure(self, mercury_tool):
        mercury_tool.client.request = AsyncMock(side_effect=Exception("API Error"))

        params = GetTransactionParams(account_id="acc_123", transaction_id="tx_123")

        with pytest.raises(Exception) as exc_info:
            await mercury_tool.get_transaction(params)
        assert str(exc_info.value) == "API Error"
