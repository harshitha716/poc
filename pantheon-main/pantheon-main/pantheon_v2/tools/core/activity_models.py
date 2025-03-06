from pydantic import BaseModel
from typing import Callable, Any, Sequence
import inspect


class Activity(BaseModel):
    name: str
    description: str
    func: Callable
    _parameters: tuple = None
    _returns: type | None = None

    @property
    def parameters(self) -> Sequence[Any]:
        if self._parameters is None:
            self._parameters = self._get_parameters()
        return self._parameters

    @property
    def returns(self) -> Any:
        if self._returns is None:
            self._returns = self._get_returns()
        return self._returns

    def _get_parameters(self) -> tuple:
        parameters = inspect.signature(self.func).parameters
        params = []
        for param_name, param in parameters.items():
            if param.annotation == inspect.Signature.empty:
                raise ValueError(f"Parameter {param_name} has no type annotation")
            params.append(param.annotation)

        return tuple(params)

    def _get_returns(self) -> type:
        return_type = inspect.signature(self.func).return_annotation
        if return_type == inspect.Signature.empty:
            raise ValueError("Return type is not specified")
        return return_type

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class ActivityExecuteParams(BaseModel):
    activity_name: str | Callable
    return_type: type | None = None
    args: tuple
