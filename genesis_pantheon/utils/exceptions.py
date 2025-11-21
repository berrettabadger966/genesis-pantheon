"""Custom exception classes for GenesisPantheon."""


class BudgetExceededError(Exception):
    """Raised when the collective's budget has been exhausted.

    Attributes:
        spent: Total amount spent at the time of the exception.
    """

    def __init__(self, spent: float, message: str) -> None:
        self.spent = spent
        super().__init__(message)


class OracleError(Exception):
    """Raised when an LLM oracle encounters an unrecoverable error."""


class DirectiveError(Exception):
    """Raised when a directive fails during execution."""


class ArenaError(Exception):
    """Raised when the arena encounters an invalid state."""


class ValidationError(Exception):
    """Raised when input validation fails in framework code."""


class SerializationError(Exception):
    """Raised when serialization or deserialization fails."""


__all__ = [
    "BudgetExceededError",
    "OracleError",
    "DirectiveError",
    "ArenaError",
    "ValidationError",
    "SerializationError",
]
