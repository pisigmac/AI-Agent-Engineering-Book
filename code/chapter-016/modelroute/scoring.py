"""Multi-objective scoring for model candidates."""

from __future__ import annotations

from modelroute.types import (
    LATENCY_RANK,
    QUALITY_RANK,
    LatencyClass,
    ModelProfile,
    QualityTier,
    RouteStrategy,
    ScoreBreakdown,
    TaskKind,
    TaskRequest,
)

# Strategy weights: (quality, cost_efficiency, latency_efficiency)
_WEIGHTS: dict[RouteStrategy, tuple[float, float, float]] = {
    RouteStrategy.QUALITY: (0.70, 0.10, 0.20),
    RouteStrategy.COST: (0.20, 0.65, 0.15),
    RouteStrategy.LATENCY: (0.20, 0.15, 0.65),
    RouteStrategy.BALANCED: (0.40, 0.35, 0.25),
    RouteStrategy.PINNED: (1.0, 0.0, 0.0),
}


def _quality_score(tier: QualityTier) -> float:
    return QUALITY_RANK[tier] / QUALITY_RANK[QualityTier.FLAGSHIP]


def _latency_score(cls: LatencyClass) -> float:
    # Faster → higher score
    return 1.0 - (LATENCY_RANK[cls] - 1) / (len(LATENCY_RANK) - 1)


def _cost_score(profile: ModelProfile, task: TaskRequest) -> float:
    """Map estimated USD to (0, 1] with cheaper better. Local $0 → 1.0."""
    cost = profile.estimated_cost_usd(task.expected_input_tokens, task.expected_output_tokens)
    if cost <= 0:
        return 1.0
    # Soft saturation: $0.05 for this request size ≈ mid; adjust via log-ish curve
    # score = 1 / (1 + cost / ref)
    ref = 0.01
    return 1.0 / (1.0 + cost / ref)


def _capability_fit(profile: ModelProfile, task: TaskRequest) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 1.0
    caps = profile.capabilities

    if not caps.supports(task.kind):
        return 0.0, ["missing_task_capability"]

    if task.require_tools and not caps.tools:
        return 0.0, ["requires_tools"]
    if task.require_json and not (caps.json_mode or caps.chat):
        return 0.0, ["requires_json"]
    if task.require_vision and not caps.vision:
        return 0.0, ["requires_vision"]
    if task.require_long_context and not caps.long_context:
        # Soft penalty if window is still large enough
        need = task.expected_input_tokens + task.expected_output_tokens + 512
        if profile.context_window < need:
            return 0.0, ["context_window_too_small"]
        score *= 0.7
        reasons.append("no_long_context_flag_but_window_ok")

    need = task.expected_input_tokens + task.expected_output_tokens + 256
    if profile.context_window < need:
        return 0.0, ["context_window_too_small"]

    if task.kind is TaskKind.CODE and caps.code:
        score = min(1.0, score + 0.05)
        reasons.append("code_capable")
    if task.kind is TaskKind.TOOL_PLAN and caps.tools:
        reasons.append("tools_capable")
    if task.kind is TaskKind.EMBED and caps.embeddings:
        reasons.append("embeddings_capable")

    return score, reasons


def eligibility(profile: ModelProfile, task: TaskRequest) -> tuple[bool, list[str]]:
    rejects: list[str] = []
    fit, fit_reasons = _capability_fit(profile, task)
    if fit <= 0:
        rejects.extend(fit_reasons or ["capability_mismatch"])

    if task.min_quality is not None:
        if QUALITY_RANK[profile.quality] < QUALITY_RANK[task.min_quality]:
            rejects.append(f"below_min_quality:{task.min_quality.value}")

    if task.max_latency_ms is not None:
        # Map latency class to rough p50 budgets for filtering
        budgets = {
            LatencyClass.FAST: 800,
            LatencyClass.STANDARD: 2500,
            LatencyClass.SLOW: 8000,
        }
        if budgets[profile.latency] > task.max_latency_ms:
            rejects.append("exceeds_max_latency")

    if task.max_cost_usd is not None:
        cost = profile.estimated_cost_usd(
            task.expected_input_tokens, task.expected_output_tokens
        )
        if cost > task.max_cost_usd:
            rejects.append("exceeds_max_cost")

    if task.pinned_model_id and profile.model_id != task.pinned_model_id:
        rejects.append("not_pinned_model")

    return (len(rejects) == 0, rejects)


def score_model(
    profile: ModelProfile,
    task: TaskRequest,
    strategy: RouteStrategy,
) -> ScoreBreakdown:
    ok, rejects = eligibility(profile, task)
    if not ok:
        return ScoreBreakdown(
            quality=0.0,
            cost=0.0,
            latency=0.0,
            capability_fit=0.0,
            total=0.0,
            reasons=tuple(rejects),
        )

    fit, fit_reasons = _capability_fit(profile, task)
    q = _quality_score(profile.quality)
    c = _cost_score(profile, task)
    lat = _latency_score(profile.latency)
    wq, wc, wl = _WEIGHTS[strategy]
    # Capability fit as a gate already applied; mild multiplier
    total = (wq * q + wc * c + wl * lat) * fit
    reasons = [
        f"strategy={strategy.value}",
        f"quality={profile.quality.value}:{q:.2f}",
        f"cost_eff={c:.2f}",
        f"latency_eff={lat:.2f}",
        *fit_reasons,
    ]
    return ScoreBreakdown(
        quality=q,
        cost=c,
        latency=lat,
        capability_fit=fit,
        total=total,
        reasons=tuple(reasons),
    )
