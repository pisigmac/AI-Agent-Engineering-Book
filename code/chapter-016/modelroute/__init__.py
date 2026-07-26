"""Model selection and routing for the evolving AI platform."""

from modelroute.catalog import catalog_by_id, default_catalog
from modelroute.classifier import build_task_request, infer_task_kind
from modelroute.completer import MockBackend, RoutedCompleter, build_default_completer
from modelroute.router import ModelRouter, NoEligibleModelError
from modelroute.types import (
    CompletionResult,
    ModelProfile,
    RouteDecision,
    RouteStrategy,
    TaskKind,
    TaskRequest,
)

__all__ = [
    "CompletionResult",
    "MockBackend",
    "ModelProfile",
    "ModelRouter",
    "NoEligibleModelError",
    "RouteDecision",
    "RouteStrategy",
    "RoutedCompleter",
    "TaskKind",
    "TaskRequest",
    "build_default_completer",
    "build_task_request",
    "catalog_by_id",
    "default_catalog",
    "infer_task_kind",
]

__version__ = "1.0.0"
