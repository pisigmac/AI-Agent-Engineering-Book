"""Chapter 11 CLI — prompt library."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from promptlib.patterns import role_preamble
from promptlib.registry import PromptRegistry, default_library_path
from promptlib.template import TemplateError
from promptlib.testing import PromptTestSuite


def _registry() -> PromptRegistry:
    return PromptRegistry.from_directory(default_library_path())


def cmd_list() -> int:
    print(json.dumps({"prompts": _registry().list()}, indent=2))
    return 0


def cmd_show(prompt_id: str, version: str | None) -> int:
    reg = _registry()
    try:
        spec = reg.get(prompt_id, version=version)
    except KeyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    payload = {
        "id": spec.id,
        "version": spec.version,
        "description": spec.description,
        "risk": spec.risk,
        "tags": list(spec.tags),
        "required_vars": list(spec.required_vars),
        "constraints": list(spec.constraints),
        "examples": len(spec.examples),
        "system": spec.system,
        "user_template": spec.user_template,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_render(prompt_id: str, var_pairs: list[str], version: str | None) -> int:
    variables: dict[str, str] = {}
    for pair in var_pairs:
        if "=" not in pair:
            print(f"ERROR: expected key=value, got {pair}", file=sys.stderr)
            return 2
        k, v = pair.split("=", 1)
        variables[k] = v
    # Convenience for support.refund demos
    if "role_line" not in variables and prompt_id == "support.refund":
        variables["role_line"] = role_preamble(
            "a careful customer support agent",
            mission="resolve refund questions using policy evidence only",
        )
    reg = _registry()
    try:
        rendered = reg.render(prompt_id, variables, version=version)
    except (KeyError, TemplateError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(rendered.to_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_test() -> int:
    suite = PromptTestSuite(_registry())
    report = suite.run()
    print(json.dumps(report.to_dict(), indent=2))
    return 0 if report.passed else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 11 — prompt library CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List registered prompts")
    p_show = sub.add_parser("show", help="Show a prompt spec")
    p_show.add_argument("prompt_id")
    p_show.add_argument("--version", default=None)

    p_ren = sub.add_parser("render", help="Render a prompt with variables")
    p_ren.add_argument("prompt_id")
    p_ren.add_argument("--var", action="append", default=[], help="key=value (repeatable)")
    p_ren.add_argument("--version", default=None)

    sub.add_parser("test", help="Run static prompt test suite")

    args = parser.parse_args(argv)
    if args.cmd == "list":
        return cmd_list()
    if args.cmd == "show":
        return cmd_show(args.prompt_id, args.version)
    if args.cmd == "render":
        return cmd_render(args.prompt_id, args.var, args.version)
    if args.cmd == "test":
        return cmd_test()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
