"""Custom exceptions for the Dota 2 match observer."""

class DotaAPIError(Exception):
    """Base exception for API-related errors."""
    pass


class RateLimitError(DotaAPIError):
    """Raised when API rate limit is exceeded."""
    pass


class DatabaseError(Exception):
    """Base exception for database-related errors."""
    pass


class MatchNotFoundError(DotaAPIError):
    """Raised when a match is not found."""
    pass
