class DataSourceError(Exception):
    """Base exception for data source errors."""
    pass

class RateLimitError(DataSourceError):
    """Raised when rate limit is exceeded."""
    pass

class APIError(DataSourceError):
    """Raised when API returns an error."""
    pass

class ValidationError(DataSourceError):
    """Raised when data validation fails."""
    pass

class ConnectionError(DataSourceError):
    """Raised when connection to data source fails."""
    pass