from pydantic import BaseModel
from typing import Dict, Any


class Error(BaseModel):
    message: str
    code: str
    path: str
    internal_metadata: Dict[str, Any]
    external_metadata: Dict[str, Any]
    exception: Exception

    @staticmethod
    def from_exception(exception: Exception) -> "Error":
        return Error(
            message=str(exception),
            code=str(exception.__class__.__name__),
            path=str(exception.__traceback__),
            internal_metadata={},
            external_metadata={},
            exception=exception,
        )

    def add_internal_metadata(self, dictionary: Dict[str, Any]) -> None:
        self.internal_metadata.update(dictionary)

    def add_external_metadata(self, dictionary: Dict[str, Any]) -> None:
        self.external_metadata.update(dictionary)
