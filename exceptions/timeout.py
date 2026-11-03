class TimeoutButSuccessException(Exception):
    """Raised when a timeout occurs but the operation was successful."""


class TimeoutNotSuccessException(Exception):
    """Raised when a timeout occurs and the operation was not successful."""
