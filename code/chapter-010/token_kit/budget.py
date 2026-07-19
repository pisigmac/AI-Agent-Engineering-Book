"""Effective context budget calculations."""

from __future__ import annotations

from token_kit.types import BudgetConfig


def effective_input_budget(config: BudgetConfig) -> int:
    """Tokens available for packed prompt messages (not including completion)."""
    budget = (
        config.context_window
        - config.max_completion
        - config.margin
        - config.reserved_system
        - config.reserved_tools
    )
    return max(0, budget)


def fits(tokens: int, config: BudgetConfig) -> bool:
    return tokens <= effective_input_budget(config)


def utilization(tokens: int, config: BudgetConfig) -> float:
    budget = effective_input_budget(config)
    if budget <= 0:
        return 1.0
    return min(1.0, tokens / budget)
