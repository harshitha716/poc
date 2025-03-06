import structlog
from typing import Optional
import random

from pantheon_v2.tools.core.base import BaseTool
from pantheon_v2.tools.core.tool_registry import ToolRegistry
from pantheon_v2.tools.external.mercury.config import MercuryConfig
from pantheon_v2.tools.external.mercury.models import (
    Transaction,
    CreateTransactionRequest,
    GetTransactionParams,
)
from pantheon_v2.utils.api_client import ApiClient, HttpMethod
from pantheon_v2.tools.external.mercury.constants import (
    MERCURY_BASE_URL,
    DEFAULT_HEADERS,
    AUTHORIZATION_HEADER_FORMAT,
    HEADER_KEY_AUTHORIZATION,
)

logger = structlog.get_logger(__name__)


@ToolRegistry.register_tool(
    description="Mercury banking API tool for managing transactions",
)
class MercuryTool(BaseTool):
    def __init__(self, config: dict):
        self.config: Optional[MercuryConfig] = config
        self.client: Optional[ApiClient] = None

    async def initialize(self) -> None:
        """Initialize the Mercury API client"""
        try:
            logger.info("Initializing Mercury tool")
            self.config = MercuryConfig(**self.config)
            headers = DEFAULT_HEADERS.copy()
            headers[HEADER_KEY_AUTHORIZATION] = AUTHORIZATION_HEADER_FORMAT.format(
                self.config.api_key
            )
            self.client = ApiClient(
                base_url=MERCURY_BASE_URL,
                default_headers=headers,
            )
            logger.info("Mercury tool initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Mercury tool", error=str(e))
            raise

    @ToolRegistry.register_tool_action(description="Create a new transaction")
    async def create_transaction(self, params: CreateTransactionRequest) -> Transaction:
        """Create a new transaction in Mercury"""
        try:
            # TODO: Fix this later, this is only for netflix demo.
            adjusted_amount = params.amount + (random.randint(0, 99) / 100)
            request_data = {
                "recipientId": params.recipient_id,
                "amount": adjusted_amount,
                "paymentMethod": params.payment_method,
                "idempotencyKey": params.idempotency_key,
            }
            logger.info(f"Mercury Request data: {request_data}")
            return await self.client.request(
                method=HttpMethod.POST,
                endpoint=f"/account/{params.account_id}/transactions",
                response_model=Transaction,
                data=request_data,
            )
        except Exception as e:
            logger.error("Failed to create transaction", error=str(e))
            raise

    @ToolRegistry.register_tool_action(description="Get transaction by ID")
    async def get_transaction(self, params: GetTransactionParams) -> Transaction:
        """Retrieve a transaction by ID"""
        try:
            response = await self.client.request(
                method=HttpMethod.GET,
                endpoint=f"/account/{params.account_id}/transaction/{params.transaction_id}",
                response_model=Transaction,
            )
            logger.info("Transaction fetched successfully", transaction=response)
            return response
        except Exception as e:
            logger.error("Failed to get transaction", error=str(e))
            raise
