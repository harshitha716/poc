import pytest
from pantheon_v2.processes.core.business_logic_registry import (
    BusinessLogicRegistry,
)


@BusinessLogicRegistry.register_business_logic("Add two numbers", ["test"])
async def business_logic_1(a: int, b: int) -> int:
    return a + b


@BusinessLogicRegistry.register_business_logic("Multiply two numbers", ["test"])
async def business_logic_2(a: int, b: int) -> int:
    return a * b


@pytest.mark.asyncio
async def test_business_logic_registry():
    assert await business_logic_1(1, 2) == 3
    assert await business_logic_2(1, 2) == 2


@pytest.mark.asyncio
async def test_business_logic_registry_get_business_logic_by_labels():
    business_logics = BusinessLogicRegistry.get_business_logic_by_labels(["test"])
    assert len(business_logics) == 2
    assert business_logics[0].name == "business_logic_1"
    assert business_logics[1].name == "business_logic_2"
