from enum import StrEnum


class Actions(StrEnum):
    GET_HERM_FORMULA = "GET_HERM_FORMULA"

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)


class Status(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)
