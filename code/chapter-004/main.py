"""Chapter 4 CLI — Git workflow toolkit."""

from __future__ import annotations

import argparse
import subprocess
import sys

from branch_validator import validate_branch_name
from change_inventory import inventory_paths
from commit_validator import validate_commit_message


def _git_lines(args: list[str]) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", *args],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [ln for ln in out.splitlines() if ln.strip()]


def cmd_check_commit(message: str) -> int:
    result = validate_commit_message(message)
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    if not result.ok:
        for error in result.errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: commit message")
    return 0


def cmd_check_branch(name: str | None) -> int:
    if not name:
        lines = _git_lines(["rev-parse", "--abbrev-ref", "HEAD"])
        name = lines[0] if lines else ""
    result = validate_branch_name(name)
    if not result.ok:
        for error in result.errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: branch '{name}'")
    return 0


def cmd_inventory(base: str) -> int:
    paths = _git_lines(["diff", "--name-only", f"{base}...HEAD"])
    if not paths:
        paths = _git_lines(["diff", "--name-only"]) + _git_lines(
            ["diff", "--name-only", "--cached"]
        )
        paths = sorted(set(paths))
    inventory = inventory_paths(paths)
    if not paths:
        print("No changed files detected.")
        return 0
    print(f"Changed files: {len(paths)}")
    for line in inventory.summary_lines():
        print(f"  • {line}")
    if "source_of_truth" in inventory.areas:
        print("NOTE: source-of-truth docs changed — elevate review standards.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 4 — Git workflow toolkit")
    sub = parser.add_subparsers(dest="cmd", required=True)

    check_commit = sub.add_parser(
        "check-commit", help="Validate a conventional commit message"
    )
    check_commit.add_argument("message")

    check_branch = sub.add_parser(
        "check-branch", help="Validate branch name (default: current)"
    )
    check_branch.add_argument("name", nargs="?", default=None)

    inventory = sub.add_parser("inventory", help="Summarize changed paths vs base")
    inventory.add_argument("--base", default="main", help="Diff base ref (default: main)")

    args = parser.parse_args(argv)
    if args.cmd == "check-commit":
        return cmd_check_commit(args.message)
    if args.cmd == "check-branch":
        return cmd_check_branch(args.name)
    if args.cmd == "inventory":
        return cmd_inventory(args.base)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
