from pantheon_v2.core.temporal.workflows.registry import get_registered_workflows
from pantheon_v2.core.temporal.activities.registry import get_registered_activities

import pytest


@pytest.mark.asyncio
def test_get_registered_workflows():
    workflows = get_registered_workflows()
    assert len(workflows) > 0


@pytest.mark.asyncio
def test_get_registered_activities():
    activities = get_registered_activities()
    assert len(activities) > 0
