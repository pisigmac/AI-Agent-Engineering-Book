"""Typed errors and severity vocabulary."""

from __future__ import annotations

from enum import Enum


class Severity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PlatformError(Exception):
    def __init__(self, message: str, *, severity: Severity = Severity.ERROR) -> None:
        super().__init__(message)
        self.severity = severity


class ValidationError(PlatformError):
    def __init__(self, message: str) -> None:
        super().__init__(message, severity=Severity.WARNING)


class TransientError(PlatformError):
    def __init__(self, message: str) -> None:
        super().__init__(message, severity=Severity.ERROR)
