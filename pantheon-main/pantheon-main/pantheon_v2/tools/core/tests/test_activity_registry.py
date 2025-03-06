import pytest
from pantheon_v2.tools.core.activity_registry import ActivityRegistry
from pantheon_v2.tools.core.activity_models import ActivityExecuteParams
from unittest.mock import patch


@pytest.fixture
def a() -> str:
    return "test"


# Define a regular method instead of a test function
@ActivityRegistry.register_activity("test_activity")
async def test_activity(a: str) -> str:
    return a


@pytest.mark.asyncio
async def test_tool_registry_execute_tool_action():
    with patch("temporalio.workflow.execute_activity") as mock_execute_activity:
        mock_execute_activity.return_value = "test"
        tool_action = await ActivityRegistry.execute_activity(
            ActivityExecuteParams(
                activity_name="test_activity",
                args=("test",),
                kwargs={},
            )
        )

    assert tool_action == "test"


@pytest.mark.asyncio
async def test_unique_activity_name():
    with pytest.raises(ValueError):

        @ActivityRegistry.register_activity("test_activity")
        async def test_activity():
            return "test"


async def test_unique_activity_name_with_same_name():
    from pantheon_v2.tools import exposed_activities

    unique_activity_names = set()
    for activity in exposed_activities:
        # check if the activity name is unique
        if activity.__name__ in unique_activity_names:
            raise ValueError(f"Activity '{activity.__name__}' is not unique")
        unique_activity_names.add(activity.__name__)


@pytest.mark.asyncio
async def test_activity_details():
    details = ActivityRegistry.get_activity_details("execute_code")
    assert details.name == "execute_code"


@pytest.mark.asyncio
async def test_activity_details_not_found():
    with pytest.raises(ValueError):

        @ActivityRegistry.register_activity("test_activity")
        async def brr_activity(a) -> str:
            return "test"

    with pytest.raises(ValueError):

        @ActivityRegistry.register_activity("brr_activity_2")
        async def brr_activity_2(a: str):
            return "190"

    @ActivityRegistry.register_activity("brr_activity_3")
    async def brr_activity_3(a: str) -> str:
        return "190"

    details = ActivityRegistry.get_activity_details("brr_activity_3")
    assert details.name == "brr_activity_3"
    assert details.parameters == (str,)
    assert isinstance(details.returns, type(str))
