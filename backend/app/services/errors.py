class ApiError(Exception):
    """Base class for errors that should be surfaced to the client with a clean message."""

    status_code = 400

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class WorkflowError(ApiError):
    """Raised when a requested state transition is not allowed."""

    status_code = 400


class ForbiddenError(ApiError):
    status_code = 403


class NotFoundError(ApiError):
    status_code = 404
