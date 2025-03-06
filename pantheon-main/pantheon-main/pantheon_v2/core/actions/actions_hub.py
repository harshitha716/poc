from pantheon_v2.tools.core.activity_registry import ActivityRegistry
from pantheon_v2.processes.core.registry import WorkflowRegistry
from pantheon_v2.processes.core.business_logic_registry import BusinessLogicRegistry
from pantheon_v2.core.actions.models import Action, ActionFilter


class ActionsHub:
    @classmethod
    def get_available_actions(cls, filters: ActionFilter) -> list[Action]:
        actions = []
        workflows = WorkflowRegistry.get_available_workflows(filters.labels)
        for workflow in workflows:
            actions.append(Action.from_workflow(workflow))

        for activity in ActivityRegistry.get_available_activities():
            actions.append(Action.from_activity(activity))

        for business_logic in BusinessLogicRegistry.get_available_business_logic_list():
            actions.append(Action.from_business_logic(business_logic))

        return filters.filter_actions(actions)

    @classmethod
    def execute_action(cls, action_name: str, *args, **kwargs):
        action = cls.get_available_actions(ActionFilter(name=action_name))
        if len(action) == 0:
            raise ValueError(f"Action {action_name} not found")

        return action[0].execute(*args, **kwargs)
