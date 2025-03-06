from pantheon_v2.tools.common.contract_data_extracter.tool import (
    ContractDataExtracterTool,
)

from pantheon_v2.tools.common.contract_data_extracter.models import (
    ContractDataExtracterInput,
    ContractDataExtracterOutput,
)

from pantheon_v2.tools.core.activity_registry import ActivityRegistry


@ActivityRegistry.register_activity("extract_contract_data")
async def extract_contract_data(
    params: ContractDataExtracterInput,
) -> ContractDataExtracterOutput:
    tool = ContractDataExtracterTool()
    await tool.initialize()
    return await tool.extract_data(params)
