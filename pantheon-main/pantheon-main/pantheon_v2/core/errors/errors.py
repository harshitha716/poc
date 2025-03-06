from temporalio.exceptions import ApplicationError

from pantheon_v2.core.errors.base import Error


class RetryableError(Error, ApplicationError):
    def __init__(self, exception: Exception):
        super().__init__(exception)
        super().__init__(exception.message)
        self.non_retryable = False

    @staticmethod
    def from_exception(exception: Exception) -> "RetryableError":
        return RetryableError(exception)


class NonRetryableError(Error, ApplicationError):
    def __init__(self, exception: Exception):
        super().__init__(exception)
        super().__init__(exception.message)
        self.non_retryable = True

    @staticmethod
    def from_exception(exception: Exception) -> "NonRetryableError":
        return NonRetryableError(exception)
