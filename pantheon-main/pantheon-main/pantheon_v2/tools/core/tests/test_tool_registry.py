import pytest
from pantheon_v2.tools.core.tool_registry import ToolRegistry
from pantheon_v2.tools.core.base import BaseTool


@ToolRegistry.register_tool("This is a test tool")
class TestTool(BaseTool):
    def __init__(self):
        pass

    async def initialize(self, config):
        pass

    @ToolRegistry.register_tool_action("This is a test tool action")
    async def test_action():
        return "test"


@pytest.mark.asyncio
async def test_tool_registry_registration():
    # Check if tool was registered
    assert "TestTool" in ToolRegistry._tools
    tool = ToolRegistry._tools["TestTool"]
    assert tool.description == "This is a test tool"

    # Check if action was registered
    action = await tool.get_action("test_action")()
    assert action == "test"


@pytest.mark.asyncio
async def test_tool_registry_execute_tool_action():
    tool_action = await ToolRegistry.execute_tool_action("TestTool", "test_action")
    assert tool_action == "test"


@pytest.mark.asyncio
async def test_tool_registry_execute_tool_action_not_found():
    with pytest.raises(ValueError):
        await ToolRegistry.execute_tool_action("TestTool", "test_action_not_found")


@pytest.mark.asyncio
async def test_tool_registry_execute_tool_not_found():
    with pytest.raises(ValueError):
        await ToolRegistry.execute_tool_action("TestTool", "test_action_not_founds")
