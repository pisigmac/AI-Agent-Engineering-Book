"""Public facade for context assembly."""

from __future__ import annotations

from contextkit.assemble import AssemblyError, build_result, select_items
from contextkit.sources import materialize
from contextkit.tokens import ApproxTokenEstimator, TokenEstimator
from contextkit.types import AssemblyResult, ContextState

# Re-export for callers
__all__ = ["AssemblyError", "ContextManager"]


class ContextManager:
    """Assemble a budgeted, trust-aware message list from agent state."""

    def __init__(
        self,
        estimator: TokenEstimator | None = None,
        *,
        max_tokens_tool: int = 800,
        max_tokens_memory: int = 600,
    ) -> None:
        self.estimator = estimator or ApproxTokenEstimator()
        self.max_tokens_tool = max_tokens_tool
        self.max_tokens_memory = max_tokens_memory

    def assemble(self, state: ContextState, budget: int) -> AssemblyResult:
        items = materialize(state)
        kept, dropped, compressed_ids, notes = select_items(
            items,
            self.estimator,
            budget=budget,
            max_tokens_tool=self.max_tokens_tool,
            max_tokens_memory=self.max_tokens_memory,
        )
        return build_result(
            kept,
            dropped,
            budget=budget,
            estimator=self.estimator,
            compressed_ids=compressed_ids,
            notes=notes,
            policy_id=state.policy_id,
        )
