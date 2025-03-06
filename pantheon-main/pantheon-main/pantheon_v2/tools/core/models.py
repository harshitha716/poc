from typing import Callable, List


class Tool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.actions: List[ToolAction] = []

    def add_action(self, name: str, action: Callable, description: str):
        self.actions.append(ToolAction(name, action, description))

    def get_action(self, action_name: str):
        for action in self.actions:
            if action.name == action_name:
                return action
        return None


class ToolAction:
    def __init__(self, name: str, func: Callable, description: str):
        self.name = name
        self.func = func
        self.description = description

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
