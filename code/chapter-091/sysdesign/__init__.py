"""AI system design helpers: capacity, latency budgets, design checklist."""
from .design import (
    CapacityEstimate,
    DesignChecklist,
    LatencyBudget,
    SystemDesignKit,
    estimate_capacity,
)

__all__ = [
    "CapacityEstimate",
    "DesignChecklist",
    "LatencyBudget",
    "SystemDesignKit",
    "estimate_capacity",
]
__version__ = "1.0.0"
