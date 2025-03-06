from typing import List
from zamp_public_workflow_sdk.temporal.temporal_worker import Activity
from pantheon_v2.tools import exposed_activities


def get_registered_activities() -> List[Activity]:
    """Returns a list of all registered activities."""
    activities = []
    for activity in exposed_activities:
        activities.append(Activity(name=activity.__name__, func=activity))

    return activities
