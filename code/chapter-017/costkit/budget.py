"""Spend and token budgets with fail-closed checks."""

from __future__ import annotations

from costkit.types import Budget, BudgetStatus, TokenUsage, UsageEvent


class BudgetExceeded(RuntimeError):
    def __init__(self, status: BudgetStatus) -> None:
        super().__init__(f"budget exceeded: {status.violations}")
        self.status = status


class BudgetTracker:
    def __init__(self, budget: Budget) -> None:
        self.budget = budget
        self.spent_usd = 0.0
        self.input_tokens = 0
        self.output_tokens = 0
        self.calls = 0

    def status(self) -> BudgetStatus:
        violations: list[str] = []
        b = self.budget
        if b.max_cost_usd is not None and self.spent_usd > b.max_cost_usd + 1e-15:
            violations.append("max_cost_usd")
        if b.max_input_tokens is not None and self.input_tokens > b.max_input_tokens:
            violations.append("max_input_tokens")
        if b.max_output_tokens is not None and self.output_tokens > b.max_output_tokens:
            violations.append("max_output_tokens")
        if b.max_calls is not None and self.calls > b.max_calls:
            violations.append("max_calls")
        return BudgetStatus(
            budget=b,
            spent_usd=self.spent_usd,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            calls=self.calls,
            ok=len(violations) == 0,
            violations=violations,
        )

    def check(self) -> BudgetStatus:
        st = self.status()
        if not st.ok:
            raise BudgetExceeded(st)
        return st

    def would_exceed(self, *, cost_usd: float = 0.0, usage: TokenUsage | None = None) -> list[str]:
        usage = usage or TokenUsage()
        b = self.budget
        violations: list[str] = []
        if b.max_cost_usd is not None and self.spent_usd + cost_usd > b.max_cost_usd + 1e-15:
            violations.append("max_cost_usd")
        if b.max_input_tokens is not None and self.input_tokens + usage.input_tokens > b.max_input_tokens:
            violations.append("max_input_tokens")
        if b.max_output_tokens is not None and self.output_tokens + usage.output_tokens > b.max_output_tokens:
            violations.append("max_output_tokens")
        if b.max_calls is not None and self.calls + 1 > b.max_calls:
            violations.append("max_calls")
        return violations

    def reserve_or_raise(self, *, cost_usd: float, usage: TokenUsage) -> None:
        bad = self.would_exceed(cost_usd=cost_usd, usage=usage)
        if bad:
            st = self.status()
            st.ok = False
            st.violations = bad
            raise BudgetExceeded(st)

    def record(self, event: UsageEvent) -> BudgetStatus:
        # Cache hits still count as calls for rate of use, but cost may be 0
        self.calls += 1
        self.spent_usd += event.cost_usd
        self.input_tokens += event.usage.input_tokens
        self.output_tokens += event.usage.output_tokens
        return self.check()
