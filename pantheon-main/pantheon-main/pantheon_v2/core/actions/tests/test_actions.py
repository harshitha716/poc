import pytest
from pydantic import BaseModel, Field
from pantheon_v2.tools.core.activity_registry import ActivityRegistry
from pantheon_v2.core.actions.actions_hub import ActionsHub
from pantheon_v2.core.actions.models import ActionFilter


class SampleModel(BaseModel):
    name: str = Field(description="The name of the person")
    age: int = Field(description="The age of the person")


@ActivityRegistry.register_activity("Sample activity")
def sample_activity_test_models(name: SampleModel) -> SampleModel:
    return name


@pytest.mark.asyncio
async def test_get_json_output():
    actions = ActionsHub.get_available_actions(
        ActionFilter(resticted_action_set=["sample_activity_test_models"])
    )

    json_output = actions[0].get_model_schema()
    assert json_output == {
        "args": [
            [
                {
                    "name": "name",
                    "type": "str",
                    "description": "The name of the person",
                },
                {"name": "age", "type": "int", "description": "The age of the person"},
            ]
        ],
        "returns": [
            {"name": "name", "type": "str", "description": "The name of the person"},
            {"name": "age", "type": "int", "description": "The age of the person"},
        ],
    }
