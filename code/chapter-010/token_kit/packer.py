"""Priority-aware context packer with audit trail."""

from __future__ import annotations

from token_kit.budget import effective_input_budget
from token_kit.compress import cap_tool_messages
from token_kit.tokenizers import TokenCounter
from token_kit.types import BudgetConfig, ChatMessage, PackResult, Priority, Role


_PRIORITY_RANK = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.NORMAL: 2,
    Priority.LOW: 3,
}


class ContextPacker:
    """Pack chat messages under a token budget.

    Strategy:
    1. Optionally cap tool payloads.
    2. Pin system messages when ``pin_system`` is true.
    3. While over budget, drop lowest-priority then oldest non-system message.
    4. Preserve chronological order of survivors.
    """

    def __init__(
        self,
        counter: TokenCounter,
        *,
        pin_system: bool = True,
        cap_tools: bool = True,
        max_tokens_per_tool: int = 1024,
    ) -> None:
        self.counter = counter
        self.pin_system = pin_system
        self.cap_tools = cap_tools
        self.max_tokens_per_tool = max_tokens_per_tool

    def pack(
        self,
        messages: list[ChatMessage],
        config: BudgetConfig,
    ) -> PackResult:
        notes: list[str] = []
        working = list(messages)
        if self.cap_tools:
            working = cap_tool_messages(
                working, self.counter, max_tokens_per_tool=self.max_tokens_per_tool
            )
            notes.append(f"tool_cap={self.max_tokens_per_tool}")

        budget = effective_input_budget(config)
        if budget <= 0:
            return PackResult(
                kept=[],
                dropped=working,
                tokens_est=0,
                budget=budget,
                over_budget=True,
                notes=notes + ["effective_budget_zero"],
                tokenizer=self.counter.name,
            )

        kept = list(working)
        dropped: list[ChatMessage] = []
        tokens_est = self.counter.count_messages(kept) if kept else 0
        if tokens_est <= budget:
            return PackResult(
                kept=kept,
                dropped=[],
                tokens_est=tokens_est,
                budget=budget,
                over_budget=False,
                notes=notes + ["no_drop_needed"],
                tokenizer=self.counter.name,
            )

        def is_pinned(msg: ChatMessage) -> bool:
            return self.pin_system and msg.role is Role.SYSTEM

        # Drop until fit (or only pinned remain and still overflow).
        for _ in range(len(working) + 1):
            tokens_est = self.counter.count_messages(kept) if kept else 0
            if tokens_est <= budget:
                break
            candidates = [(idx, msg) for idx, msg in enumerate(kept) if not is_pinned(msg)]
            if not candidates:
                notes.append("system_exceeds_budget")
                break
            # Drop lowest priority first; among ties, oldest (smallest index).
            drop_idx, _ = max(
                candidates,
                key=lambda pair: (
                    _PRIORITY_RANK[pair[1].default_priority()],
                    -pair[0],
                ),
            )
            dropped.append(kept.pop(drop_idx))

        order = {id(m): i for i, m in enumerate(working)}
        dropped.sort(key=lambda m: order.get(id(m), 0))

        tokens_est = self.counter.count_messages(kept) if kept else 0
        over = tokens_est > budget
        if dropped:
            notes.append(f"dropped={len(dropped)}")
        return PackResult(
            kept=kept,
            dropped=dropped,
            tokens_est=tokens_est,
            budget=budget,
            over_budget=over,
            notes=notes,
            tokenizer=self.counter.name,
        )
