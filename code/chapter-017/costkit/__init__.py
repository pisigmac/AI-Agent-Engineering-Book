"""Cost & performance control plane for the AI platform."""

from costkit.budget import BudgetExceeded, BudgetTracker
from costkit.cache import ResponseCache, make_cache_key
from costkit.dashboard import build_dashboard
from costkit.engine import CompleteRequest, CompleteResponse, CostEngine
from costkit.pricing import PriceBook
from costkit.types import Budget, DashboardSnapshot, TokenUsage, UsageEvent

__all__ = [
    "Budget",
    "BudgetExceeded",
    "BudgetTracker",
    "CompleteRequest",
    "CompleteResponse",
    "CostEngine",
    "DashboardSnapshot",
    "PriceBook",
    "ResponseCache",
    "TokenUsage",
    "UsageEvent",
    "build_dashboard",
    "make_cache_key",
]

__version__ = "1.0.0"
