"""Chapter 13 CLI — structured outputs demos."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from structured.complete import StructuredCompleter
from structured.extract import extract_json_object
from structured.mock_llm import MockLLM
from structured.schema_models import RefundAssessment, RouteDecision, model_to_json_schema
from structured.types import StructureParseError


def cmd_extract(text: str) -> int:
    try:
        data = extract_json_object(text)
    except StructureParseError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps({"ok": True, "value": data}, indent=2))
    return 0


def cmd_schema(name: str) -> int:
    mapping = {
        "RouteDecision": RouteDecision,
        "RefundAssessment": RefundAssessment,
    }
    if name not in mapping:
        print(f"Unknown model {name}. Choose from {list(mapping)}", file=sys.stderr)
        return 2
    print(json.dumps(model_to_json_schema(mapping[name]), indent=2))
    return 0


def cmd_route(message: str) -> int:
    # Scripted: first response invalid confidence, repair fixes it.
    llm = MockLLM(
        script=[
            (
                "validation",
                json.dumps(
                    {
                        "intent": "shipping",
                        "confidence": 1.0,
                        "needs_human": False,
                        "rationale": "Mentions package delivery status.",
                    }
                ),
            ),
            (
                "package",
                json.dumps(
                    {
                        "intent": "shipping",
                        "confidence": 1.5,
                        "needs_human": False,
                        "rationale": "Mentions package.",
                    }
                ),
            ),
            (
                "refund",
                json.dumps(
                    {
                        "intent": "refund",
                        "confidence": 0.9,
                        "needs_human": False,
                        "rationale": "Customer asks for money back.",
                    }
                ),
            ),
        ],
        default=json.dumps(
            {
                "intent": "other",
                "confidence": 0.4,
                "needs_human": True,
                "rationale": "Unclear request.",
            }
        ),
    )
    completer = StructuredCompleter(llm.generate, max_repairs=2, model_name="mock-route")
    messages = [
        {
            "role": "system",
            "content": "Classify support messages. Output JSON only.",
        },
        {"role": "user", "content": message},
    ]
    result = completer.complete(messages, RouteDecision)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.ok else 1


def cmd_refund(doc_path: Path) -> int:
    doc = doc_path.read_text(encoding="utf-8")
    # First attempt missing evidence (invalid min business rule via empty list ok),
    # use invalid decision to force repair, then good object.
    llm = MockLLM(
        script=[
            (
                "corrected json",
                json.dumps(
                    {
                        "decision": "deny",
                        "order_id": "A-100",
                        "reason_code": "outside_window",
                        "evidence": [
                            "purchased 45 days ago",
                            "refunds are available within 30 days of purchase",
                        ],
                        "needs_human": False,
                        "confidence": 0.88,
                    }
                ),
            ),
            (
                "order",
                json.dumps(
                    {
                        "decision": "approve",
                        "order_id": "A-100",
                        "reason_code": "customer_request",
                        "evidence": [],
                        "needs_human": False,
                        "confidence": 1.7,
                    }
                ),
            ),
        ]
    )
    completer = StructuredCompleter(llm.generate, max_repairs=2, model_name="mock-refund")
    messages = [
        {
            "role": "system",
            "content": (
                "Assess refunds using only the document. "
                "If outside 30 days, decision=deny. JSON only."
            ),
        },
        {"role": "user", "content": f"DOCUMENT:\n{doc}"},
    ]
    result = completer.complete(messages, RefundAssessment)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 13 — structured outputs")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ex = sub.add_parser("extract", help="Extract JSON object from text")
    p_ex.add_argument("--text", required=True)

    p_schema = sub.add_parser("schema", help="Print JSON Schema for a model")
    p_schema.add_argument("name", choices=["RouteDecision", "RefundAssessment"])

    p_route = sub.add_parser("route", help="Structured route decision demo")
    p_route.add_argument("--message", required=True)

    p_ref = sub.add_parser("refund", help="Structured refund assessment demo")
    p_ref.add_argument("--doc", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.cmd == "extract":
        return cmd_extract(args.text)
    if args.cmd == "schema":
        return cmd_schema(args.name)
    if args.cmd == "route":
        return cmd_route(args.message)
    if args.cmd == "refund":
        return cmd_refund(args.doc)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
