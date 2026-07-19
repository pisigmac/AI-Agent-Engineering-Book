"""Chapter 2 CLI — AI engineering roadmap atlas."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

CHAPTER1 = Path(__file__).resolve().parents[1] / "chapter-001"
if CHAPTER1.is_dir():
    sys.path.insert(0, str(CHAPTER1))

from canonical_stack import build_canonical_stack
from placement import place_feature
from stack_model import LayerId

try:
    from logging_setup import setup_logging
    from platform_config import Settings
except ImportError:

    def setup_logging(level: str = "INFO") -> None:
        logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))

    class Settings:  # minimal fallback
        log_level = "INFO"
        app_name = "ai-agent-platform"
        environment = "dev"

        @classmethod
        def from_env(cls, env_file: str | None = None) -> "Settings":
            return cls()


logger = logging.getLogger("platform.roadmap")


def cmd_map(*, as_mermaid: bool = False) -> int:
    stack = build_canonical_stack()
    errors = stack.validate_dependencies()
    if errors:
        for err in errors:
            logger.error("stack_invalid %s", err)
        return 1
    if as_mermaid:
        print(stack.to_mermaid(), end="")
        return 0
    print("AI Engineering Stack (canonical)\n")
    for line in stack.summarize():
        print(f"  • {line}")
    print("\nDependency check: OK")
    print(f"Layers: {len(stack.layers)}")
    return 0


def cmd_place(feature: str) -> int:
    decision = place_feature(feature)
    print(f"Feature: {feature}")
    print(f"Place at: {decision.layer.value}")
    print(f"Rationale: {decision.rationale}")
    if decision.avoid:
        print("Avoid jumping to: " + ", ".join(a.value for a in decision.avoid))
    return 0


def cmd_show(layer: str) -> int:
    stack = build_canonical_stack()
    try:
        layer_id = LayerId(layer)
    except ValueError:
        print(f"Unknown layer '{layer}'. Valid: {[x.value for x in LayerId]}")
        return 2
    item = stack.get(layer_id)
    print(f"{item.title} ({item.id.value})")
    print(f"Purpose:  {item.purpose}")
    print(f"Analogy:  {item.analogy}")
    print(f"Depends:  {[d.value for d in item.depends_on] or '—'}")
    print(f"Produces: {list(item.produces) or '—'}")
    print(f"Failures: {list(item.failure_modes) or '—'}")
    print(f"Used by:  {[d.value for d in stack.dependents_of(layer_id)] or '—'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    settings = Settings.from_env()
    setup_logging(getattr(settings, "log_level", "INFO"))

    parser = argparse.ArgumentParser(description="Chapter 2 — AI engineering roadmap CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_map = sub.add_parser("map", help="Print the canonical stack")
    p_map.add_argument(
        "--mermaid",
        action="store_true",
        help="Emit Mermaid dependency graph instead of text",
    )
    p_show = sub.add_parser("show", help="Show one layer")
    p_show.add_argument("layer", help="e.g. agent, tool, harness")
    p_place = sub.add_parser("place", help="Suggest a layer for a feature description")
    p_place.add_argument("feature", help="Natural language feature request")

    args = parser.parse_args(argv)
    if args.cmd == "map":
        return cmd_map(as_mermaid=bool(getattr(args, "mermaid", False)))
    if args.cmd == "show":
        return cmd_show(args.layer)
    if args.cmd == "place":
        return cmd_place(args.feature)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
