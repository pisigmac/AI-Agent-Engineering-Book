#!/usr/bin/env python3
"""Write scripts/data/interview_bank.yaml from catalog .txt files or rebuild catalogs first."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from interview_bank_data import (  # noqa: E402
    CATEGORY_TITLES,
    CATALOG_DIR,
    INTERMEDIATE_CATALOG_DIR,
    MIN_PER_CATEGORY,
    PREFIX_MAP,
)

OUT = SCRIPTS / "data" / "interview_bank.yaml"


def _parse_line(line: str) -> tuple[str, str, str] | None:
    line = line.strip()
    if not line or line.startswith("#") or "|" not in line:
        return None
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 2:
        return None
    q, a = parts[0], parts[1]
    diff = parts[2].lower() if len(parts) > 2 and parts[2] else "beginner"
    if diff not in ("beginner", "intermediate"):
        diff = "beginner"
    return q, a, diff


def pairs_from_catalog() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for category in CATEGORY_TITLES:
        path = CATALOG_DIR / f"{category}.txt"
        if not path.is_file():
            raise FileNotFoundError(f"Missing {path}; run build_catalog.py first")
        seq_beginner = 0
        prefix = PREFIX_MAP[category]
        for line in path.read_text(encoding="utf-8").splitlines():
            parsed = _parse_line(line)
            if not parsed:
                continue
            q, a, diff = parsed
            if diff != "beginner":
                continue
            key = q.lower()
            if key in seen:
                continue
            seen.add(key)
            seq_beginner += 1
            items.append(
                {
                    "id": f"{prefix}-{seq_beginner:03d}",
                    "category": category,
                    "difficulty": "beginner",
                    "question": q,
                    "answer": a,
                }
            )
        inter_path = INTERMEDIATE_CATALOG_DIR / f"{category}.txt"
        seq_i = 0
        if inter_path.is_file():
            for line in inter_path.read_text(encoding="utf-8").splitlines():
                parsed = _parse_line(line)
                if not parsed:
                    continue
                q, a, diff = parsed
                if diff != "intermediate":
                    diff = "intermediate"
                key = q.lower()
                if key in seen:
                    continue
                seen.add(key)
                seq_i += 1
                items.append(
                    {
                        "id": f"{prefix}-i{seq_i:03d}",
                        "category": category,
                        "difficulty": "intermediate",
                        "question": q,
                        "answer": a,
                    }
                )
    return items


def counts(items: list[dict[str, Any]]) -> dict[str, int]:
    c: dict[str, int] = {k: 0 for k in CATEGORY_TITLES}
    for it in items:
        c[it["category"]] += 1
    return c


def beginner_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    c: dict[str, int] = {k: 0 for k in CATEGORY_TITLES}
    for it in items:
        if it.get("difficulty", "beginner") == "beginner":
            c[it["category"]] += 1
    return c


def difficulty_totals(items: list[dict[str, Any]]) -> dict[str, int]:
    t: dict[str, int] = {"beginner": 0, "intermediate": 0}
    for it in items:
        d = it.get("difficulty", "beginner")
        if d in t:
            t[d] += 1
    return t


def main() -> None:
    items = pairs_from_catalog()
    bad = {k: v for k, v in beginner_counts(items).items() if v < MIN_PER_CATEGORY}
    if bad:
        raise SystemExit(f"Below {MIN_PER_CATEGORY} beginner per category: {bad}")
    payload = {
        "meta": {
            "version": 3,
            "count": len(items),
            "min_per_category": MIN_PER_CATEGORY,
            "categories": CATEGORY_TITLES,
            "counts": counts(items),
            "beginner_counts": beginner_counts(items),
            "difficulty_totals": difficulty_totals(items),
            "source": "scripts/interview_bank/catalog/*.txt + catalog/intermediate/*.txt",
        },
        "items": items,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )
    print(f"wrote {OUT} ({len(items)} items)")


if __name__ == "__main__":
    main()
