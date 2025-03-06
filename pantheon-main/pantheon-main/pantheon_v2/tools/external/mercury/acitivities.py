from pantheon_v2.tools.external.mercury.tool import MercuryTool
from pantheon_v2.tools.external.mercury.config import MercuryConfig
from pantheon_v2.tools.external.mercury.models import (
    CreateTransactionRequest,
    Transaction,
    GetTransactionParams,
)

from pantheon_v2.tools.core.activity_registry import ActivityRegistry


@ActivityRegistry.register_activity("Create a new transaction in Mercury")
async def create_transaction(
    config: MercuryConfig, params: CreateTransactionRequest
) -> Transaction:
    tool = MercuryTool(config)
    await tool.initialize()
    return await tool.create_transaction(params)


@ActivityRegistry.register_activity("Get transaction by ID in Mercury")
async def get_transaction(
    config: MercuryConfig, params: GetTransactionParams
) -> Transaction:
    tool = MercuryTool(config)
    await tool.initialize()
    return await tool.get_transaction(params)
