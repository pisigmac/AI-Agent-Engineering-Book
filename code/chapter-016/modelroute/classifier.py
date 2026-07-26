"""Lightweight task feature extraction from free-text prompts."""

from __future__ import annotations

import re

from modelroute.types import QualityTier, TaskKind, TaskRequest

_CODE_HINTS = re.compile(
    r"\b(python|typescript|javascript|def |class |```|stack trace|refactor|unit test)\b",
    re.I,
)
_TOOL_HINTS = re.compile(
    r"\b(call tool|function call|use the api|get_weather|search the web|execute)\b",
    re.I,
)
_JSON_HINTS = re.compile(r"\b(json|schema|extract fields|structured output)\b", re.I)
_SUM_HINTS = re.compile(r"\b(summarize|tldr|tl;dr|digest|condense)\b", re.I)
_CLASS_HINTS = re.compile(r"\b(classify|label|intent|category|route this)\b", re.I)
_REASON_HINTS = re.compile(
    r"\b(prove|step by step|reason carefully|complex|multi-hop|architecture trade-?off)\b",
    re.I,
)
_LONG_HINTS = re.compile(r"\b(entire book|100k|long document|full transcript)\b", re.I)


def infer_task_kind(prompt: str) -> TaskKind:
    if _CODE_HINTS.search(prompt):
        return TaskKind.CODE
    if _TOOL_HINTS.search(prompt):
        return TaskKind.TOOL_PLAN
    if _JSON_HINTS.search(prompt):
        return TaskKind.EXTRACT
    if _SUM_HINTS.search(prompt):
        return TaskKind.SUMMARIZE
    if _CLASS_HINTS.search(prompt):
        return TaskKind.CLASSIFY
    if _REASON_HINTS.search(prompt):
        return TaskKind.REASONING
    return TaskKind.CHAT


def estimate_tokens(text: str) -> int:
    """Rough heuristic ~4 chars/token for routing estimates (not billing)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def build_task_request(
    prompt: str,
    *,
    kind: TaskKind | None = None,
    strategy_hints: bool = True,
    **overrides: object,
) -> TaskRequest:
    """Build a TaskRequest from a prompt with optional field overrides."""
    kind = kind or infer_task_kind(prompt)
    inp = estimate_tokens(prompt)
    out = 256
    if kind is TaskKind.SUMMARIZE:
        out = min(512, max(128, inp // 4))
    elif kind is TaskKind.REASONING:
        out = 800
    elif kind is TaskKind.CODE:
        out = 600
    elif kind is TaskKind.CLASSIFY:
        out = 64

    require_tools = kind is TaskKind.TOOL_PLAN
    require_json = kind is TaskKind.EXTRACT
    require_long = bool(_LONG_HINTS.search(prompt)) or inp > 20_000
    min_quality = None
    if kind is TaskKind.REASONING:
        min_quality = QualityTier.LARGE
    elif kind is TaskKind.CODE:
        min_quality = QualityTier.MEDIUM

    kwargs: dict = {
        "kind": kind,
        "prompt": prompt,
        "expected_input_tokens": inp,
        "expected_output_tokens": out,
        "require_tools": require_tools,
        "require_json": require_json,
        "require_long_context": require_long,
        "min_quality": min_quality,
    }
    kwargs.update(overrides)
    return TaskRequest(**kwargs)  # type: ignore[arg-type]
