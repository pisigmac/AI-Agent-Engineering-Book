#!/usr/bin/env python3
"""Chapter 16 CLI — model selection and routing."""

from __future__ import annotations

import argparse
import json

from modelroute.catalog import default_catalog
from modelroute.classifier import build_task_request
from modelroute.completer import build_default_completer
from modelroute.matrix import model_score_table, strategy_matrix
from modelroute.router import ModelRouter, NoEligibleModelError
from modelroute.types import QualityTier, RouteStrategy, TaskKind


def _parse_strategy(name: str) -> RouteStrategy:
    return RouteStrategy(name)


def cmd_catalog() -> int:
    rows = []
    for p in default_catalog():
        rows.append(
            {
                "model_id": p.model_id,
                "provider": p.provider.value,
                "quality": p.quality.value,
                "latency": p.latency.value,
                "context_window": p.context_window,
                "in_$": p.input_cost_per_1m,
                "out_$": p.output_cost_per_1m,
                "tools": p.capabilities.tools,
                "embeddings": p.capabilities.embeddings,
                "open_weights": p.capabilities.open_weights,
            }
        )
    print(json.dumps({"models": rows}, indent=2))
    return 0


def cmd_route(prompt: str, strategy: str, kind: str | None, pin: str | None) -> int:
    router = ModelRouter()
    overrides: dict = {}
    if kind:
        overrides["kind"] = TaskKind(kind)
    if pin:
        overrides["pinned_model_id"] = pin
    task = build_task_request(prompt, **overrides)
    try:
        decision = router.route(task, strategy=_parse_strategy(strategy))
    except NoEligibleModelError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(decision.to_dict(), indent=2))
    return 0


def cmd_matrix(prompt: str) -> int:
    router = ModelRouter()
    task = build_task_request(prompt)
    print(json.dumps(strategy_matrix(router, task), indent=2))
    return 0


def cmd_scores(prompt: str, strategy: str) -> int:
    router = ModelRouter()
    task = build_task_request(prompt)
    print(
        json.dumps(
            {
                "strategy": strategy,
                "task_kind": task.kind.value,
                "rows": model_score_table(router, task, _parse_strategy(strategy)),
            },
            indent=2,
        )
    )
    return 0


def cmd_complete(prompt: str, strategy: str, fail: str | None) -> int:
    fails = set(fail.split(",")) if fail else set()
    completer = build_default_completer(fail_models=fails, strategy=_parse_strategy(strategy))
    task = build_task_request(prompt)
    try:
        result = completer.complete(task)
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_compare() -> int:
    """Fixed scenarios showing cost vs quality routing."""
    router = ModelRouter()
    scenarios = [
        ("Classify intent: billing", RouteStrategy.COST),
        ("Prove multi-hop architecture trade-off carefully", RouteStrategy.QUALITY),
        ("Summarize this meeting quickly", RouteStrategy.LATENCY),
        ("Refactor this python class and add unit tests", RouteStrategy.BALANCED),
        ("Use the get_weather tool for Berlin", RouteStrategy.BALANCED),
    ]
    out = []
    for prompt, strat in scenarios:
        task = build_task_request(prompt)
        d = router.route(task, strategy=strat)
        out.append(
            {
                "prompt": prompt,
                "inferred_kind": task.kind.value,
                "strategy": strat.value,
                "selected": d.selected_model_id,
                "est_cost_usd": round(d.est_cost_usd, 6),
                "latency": d.est_latency_class.value,
            }
        )
    print(json.dumps({"scenarios": out}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 16 — model selection / routing")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("catalog", help="List illustrative model catalog")

    p_r = sub.add_parser("route", help="Route a prompt to a model")
    p_r.add_argument("prompt")
    p_r.add_argument(
        "--strategy",
        choices=[s.value for s in RouteStrategy],
        default="balanced",
    )
    p_r.add_argument("--kind", choices=[k.value for k in TaskKind], default=None)
    p_r.add_argument("--pin", default=None, help="Pin to model_id")

    p_m = sub.add_parser("matrix", help="Compare strategies for one prompt")
    p_m.add_argument("prompt")

    p_s = sub.add_parser("scores", help="Score all models for a prompt")
    p_s.add_argument("prompt")
    p_s.add_argument(
        "--strategy",
        choices=[s.value for s in RouteStrategy],
        default="balanced",
    )

    p_c = sub.add_parser("complete", help="Routed mock completion with fallbacks")
    p_c.add_argument("prompt")
    p_c.add_argument(
        "--strategy",
        choices=[s.value for s in RouteStrategy],
        default="balanced",
    )
    p_c.add_argument(
        "--fail",
        default=None,
        help="Comma-separated model_ids that simulate outage",
    )

    sub.add_parser("compare", help="Demo scenarios across strategies")

    args = parser.parse_args(argv)
    if args.cmd == "catalog":
        return cmd_catalog()
    if args.cmd == "route":
        return cmd_route(args.prompt, args.strategy, args.kind, args.pin)
    if args.cmd == "matrix":
        return cmd_matrix(args.prompt)
    if args.cmd == "scores":
        return cmd_scores(args.prompt, args.strategy)
    if args.cmd == "complete":
        return cmd_complete(args.prompt, args.strategy, args.fail)
    if args.cmd == "compare":
        return cmd_compare()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
