"""Domain errors for platform_core."""


class PlatformError(Exception):
    """Base error for platform_core."""


class ProviderError(PlatformError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ValidationError(PlatformError):
    pass


class ConfigurationError(PlatformError):
    pass
