#!/usr/bin/env python3
"""CLI: list categories, search, or dump one category as JSON."""
from __future__ import annotations

import argparse
import json
import sys

from interviewbank import categories, get_by_category, get_by_difficulty, load_bank, search


def main() -> int:
    p = argparse.ArgumentParser(description="Chapter 95 interview bank")
    p.add_argument("--list-categories", action="store_true")
    p.add_argument("--category", help="slug e.g. python, agent_frameworks")
    p.add_argument("--difficulty", choices=("beginner", "intermediate"), help="filter by difficulty")
    p.add_argument("--search", help="substring search in Q&A")
    p.add_argument("--count", action="store_true", help="print total count")
    args = p.parse_args()
    bank = load_bank()
    if args.difficulty:
        bank = get_by_difficulty(args.difficulty, bank, category=args.category)
    elif args.category:
        bank = get_by_category(args.category, bank)
    if args.count:
        print(len(bank))
        return 0
    if args.list_categories:
        print(json.dumps(categories(load_bank()), indent=2))
        return 0
    if args.category and not args.difficulty:
        items = get_by_category(args.category, load_bank())
        print(json.dumps([item.__dict__ for item in items], indent=2))
        return 0
    if args.category and args.difficulty:
        items = get_by_difficulty(args.difficulty, load_bank(), category=args.category)
        print(json.dumps([item.__dict__ for item in items], indent=2))
        return 0
    if args.difficulty and not args.category:
        items = get_by_difficulty(args.difficulty, load_bank())
        print(json.dumps([item.__dict__ for item in items], indent=2))
        return 0
    if args.search:
        items = search(args.search, bank)
        print(json.dumps([item.__dict__ for item in items], indent=2))
        return 0
    p.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
