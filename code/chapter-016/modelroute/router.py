"""Model router: catalog + scoring + fallback chains."""

from __future__ import annotations

from modelroute.catalog import catalog_by_id, default_catalog
from modelroute.scoring import eligibility, score_model
from modelroute.types import (
    ModelProfile,
    RouteCandidate,
    RouteDecision,
    RouteStrategy,
    TaskRequest,
)


class NoEligibleModelError(LookupError):
    """No catalog entry satisfied hard constraints."""


class ModelRouter:
    """Selects a model for each TaskRequest under a routing strategy."""

    def __init__(
        self,
        catalog: list[ModelProfile] | None = None,
        *,
        default_strategy: RouteStrategy = RouteStrategy.BALANCED,
        fallback_depth: int = 3,
    ) -> None:
        self.catalog = list(catalog) if catalog is not None else default_catalog()
        self._by_id = catalog_by_id(self.catalog)
        self.default_strategy = default_strategy
        self.fallback_depth = max(1, fallback_depth)

    def get(self, model_id: str) -> ModelProfile:
        try:
            return self._by_id[model_id]
        except KeyError as exc:
            raise KeyError(f"unknown model_id: {model_id}") from exc

    def list_models(self) -> list[ModelProfile]:
        return list(self.catalog)

    def rank(
        self,
        task: TaskRequest,
        *,
        strategy: RouteStrategy | None = None,
    ) -> list[RouteCandidate]:
        strategy = strategy or (
            RouteStrategy.PINNED if task.pinned_model_id else self.default_strategy
        )
        candidates: list[RouteCandidate] = []
        for profile in self.catalog:
            ok, rejects = eligibility(profile, task)
            if not ok:
                candidates.append(
                    RouteCandidate(
                        model=profile,
                        score=score_model(profile, task, strategy),
                        eligible=False,
                        reject_reasons=tuple(rejects),
                    )
                )
                continue
            sc = score_model(profile, task, strategy)
            candidates.append(
                RouteCandidate(
                    model=profile,
                    score=sc,
                    eligible=True,
                    reject_reasons=(),
                )
            )
        eligible = [c for c in candidates if c.eligible]
        ineligible = [c for c in candidates if not c.eligible]
        # Higher score first; stable model_id tie-break
        eligible.sort(key=lambda c: (-c.score.total, c.model.model_id))
        return eligible + ineligible

    def route(
        self,
        task: TaskRequest,
        *,
        strategy: RouteStrategy | None = None,
    ) -> RouteDecision:
        strategy = strategy or (
            RouteStrategy.PINNED if task.pinned_model_id else self.default_strategy
        )
        ranked = self.rank(task, strategy=strategy)
        eligible = [c for c in ranked if c.eligible]
        if not eligible:
            raise NoEligibleModelError(
                "no model satisfied constraints; relax min_quality/cost/latency/capabilities"
            )
        chosen = eligible[0]
        chain = tuple(c.model.model_id for c in eligible[: self.fallback_depth])
        cost = chosen.model.estimated_cost_usd(
            task.expected_input_tokens, task.expected_output_tokens
        )
        reasons = list(chosen.score.reasons)
        reasons.insert(0, f"selected={chosen.model.model_id}")
        if len(chain) > 1:
            reasons.append(f"fallback_chain={','.join(chain[1:])}")
        return RouteDecision(
            selected_model_id=chosen.model.model_id,
            strategy=strategy,
            candidates=tuple(ranked),
            fallback_chain=chain,
            est_cost_usd=cost,
            est_latency_class=chosen.model.latency,
            reasons=tuple(reasons),
            task_kind=task.kind,
        )

    def decision_matrix(
        self,
        task: TaskRequest,
        strategies: list[RouteStrategy] | None = None,
    ) -> dict[str, RouteDecision]:
        """Compare primary picks across strategies for the same task."""
        strategies = strategies or [
            RouteStrategy.COST,
            RouteStrategy.LATENCY,
            RouteStrategy.QUALITY,
            RouteStrategy.BALANCED,
        ]
        out: dict[str, RouteDecision] = {}
        for s in strategies:
            # Ignore pin when exploring matrix unless strategy is PINNED
            t = task
            if s is not RouteStrategy.PINNED and task.pinned_model_id:
                t = TaskRequest(
                    kind=task.kind,
                    prompt=task.prompt,
                    expected_input_tokens=task.expected_input_tokens,
                    expected_output_tokens=task.expected_output_tokens,
                    require_tools=task.require_tools,
                    require_json=task.require_json,
                    require_vision=task.require_vision,
                    require_long_context=task.require_long_context,
                    max_latency_ms=task.max_latency_ms,
                    max_cost_usd=task.max_cost_usd,
                    min_quality=task.min_quality,
                    pinned_model_id=None,
                    metadata=task.metadata,
                )
            out[s.value] = self.route(t, strategy=s)
        return out
