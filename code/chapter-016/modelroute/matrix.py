"""Decision-matrix helpers for comparing models and strategies."""

from __future__ import annotations

from typing import Any

from modelroute.router import ModelRouter
from modelroute.scoring import eligibility, score_model
from modelroute.types import RouteStrategy, TaskRequest


def strategy_matrix(
    router: ModelRouter,
    task: TaskRequest,
) -> dict[str, Any]:
    decisions = router.decision_matrix(task)
    return {
        "task_kind": task.kind.value,
        "prompt_preview": task.prompt[:120],
        "strategies": {
            name: {
                "selected": d.selected_model_id,
                "est_cost_usd": round(d.est_cost_usd, 6),
                "latency": d.est_latency_class.value,
                "reasons": list(d.reasons)[:5],
            }
            for name, d in decisions.items()
        },
    }


def model_score_table(
    router: ModelRouter,
    task: TaskRequest,
    strategy: RouteStrategy = RouteStrategy.BALANCED,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for profile in router.list_models():
        sc = score_model(profile, task, strategy)
        ok, _ = eligibility(profile, task)
        cost = profile.estimated_cost_usd(
            task.expected_input_tokens, task.expected_output_tokens
        )
        rows.append(
            {
                "model_id": profile.model_id,
                "provider": profile.provider.value,
                "quality": profile.quality.value,
                "latency": profile.latency.value,
                "est_cost_usd": round(cost, 6),
                "score_total": round(sc.total, 4),
                "eligible": ok,
                "notes": list(sc.reasons)[:4],
            }
        )
    rows.sort(key=lambda r: r["score_total"], reverse=True)
    return rows
