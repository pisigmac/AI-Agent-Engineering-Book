#!/usr/bin/env python3
"""
Import Q&A from external 500_AI_QA corpus into bootcamp YAML.

Default source: ../500_AI_QA (sibling of repo) or INTERVIEW_500_AI_QA_PATH env var.

The upstream folder is a work-in-progress (prompt + Readme outline for 500 items).
This importer loads structured lists from Python modules and optional continuation
fragments, normalizes fields, and writes scripts/data/interview_bank_500_ai_qa.yaml.
"""

from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path
from typing import Any

import yaml

SCRIPTS = Path(__file__).resolve().parents[1]
REPO_ROOT = SCRIPTS.parent
DEFAULT_CANDIDATES = (
    REPO_ROOT.parent / "500_AI_QA",
    Path.home() / "Documents" / "500_AI_QA",
    REPO_ROOT / "vendor" / "500_AI_QA",
)


def _default_source() -> Path:
    for p in DEFAULT_CANDIDATES:
        if p.is_dir():
            return p
    return DEFAULT_CANDIDATES[0]
OUT_PATH = SCRIPTS / "data" / "interview_bank_500_ai_qa.yaml"

LIST_NAMES = ("complete_ai_questionnaire", "ai_questionnaire")


def resolve_source() -> Path:
    env = os.environ.get("INTERVIEW_500_AI_QA_PATH")
    if env:
        return Path(env).expanduser().resolve()
    return _default_source()


def _category_for_id(qid: int) -> str:
    """Map upstream numeric id ranges (Readme.md) to bootcamp slugs."""
    if qid <= 50:
        return "machine_learning"
    if qid <= 110:
        return "generative_ai"  # deep learning architectures
    if qid <= 170:
        return "ai_engineering"  # optimization / NLP block
    if qid <= 200:
        return "generative_ai"
    if qid <= 260:
        return "ai_engineering"  # MLOps / distributed
    if qid <= 320:
        return "agentic_ai"  # RL / multi-agent adjacent
    if qid <= 400:
        return "generative_ai"
    return "ai_engineering"


def _normalize_item(raw: dict[str, Any], source_file: str) -> dict[str, Any] | None:
    q = raw.get("question")
    a = raw.get("answer")
    if not q or not a:
        return None
    qid = int(raw.get("id", 0))
    return {
        "id": f"500-{qid:04d}",
        "category": _category_for_id(qid),
        "difficulty": "advanced",
        "tier": "advanced",
        "source": "500_ai_qa",
        "source_file": source_file,
        "upstream_id": qid,
        "question": str(q).strip(),
        "answer": str(a).strip(),
    }


def _load_from_python_list(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    for name in LIST_NAMES:
        if name not in text:
            continue
        ns: dict[str, Any] = {}
        try:
            exec(compile(text, str(path), "exec"), ns)  # noqa: S102 — trusted local import path
        except SyntaxError as e:
            print(f"skip {path.name} ({name}): syntax error {e}")
            continue
        lst = ns.get(name)
        if isinstance(lst, list):
            out: list[dict[str, Any]] = []
            for row in lst:
                if isinstance(row, dict):
                    item = _normalize_item(row, path.name)
                    if item:
                        out.append(item)
            return out
    return []


def _load_from_continuation_strings(path: Path) -> list[dict[str, Any]]:
    """Extract dict literals embedded in continuation_part* triple-quoted strings."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if "continuation_part" not in text and '"id":' not in text:
        return []

    # Match small dict blocks: { "id": N, "question": "...", "answer": """...""" }
    pattern = re.compile(
        r'\{\s*"id"\s*:\s*(\d+)\s*,\s*"question"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"answer"\s*:\s*"""([\s\S]*?)"""\s*\}',
        re.MULTILINE,
    )
    out: list[dict[str, Any]] = []
    for m in pattern.finditer(text):
        raw = {"id": int(m.group(1)), "question": m.group(2), "answer": m.group(3)}
        item = _normalize_item(raw, path.name)
        if item:
            out.append(item)
    return out


def collect_items(source: Path) -> list[dict[str, Any]]:
    if not source.is_dir():
        raise FileNotFoundError(f"500_AI_QA directory not found: {source}")

    seen: set[tuple[str, int]] = set()
    items: list[dict[str, Any]] = []

    for py in sorted(source.glob("*.py")):
        for batch in (_load_from_python_list(py), _load_from_continuation_strings(py)):
            for item in batch:
                key = (item["source_file"], item["upstream_id"])
                if key in seen:
                    continue
                seen.add(key)
                items.append(item)

    items.sort(key=lambda x: (x["upstream_id"], x["source_file"]))
    return items


def category_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for it in items:
        c = it["category"]
        counts[c] = counts.get(c, 0) + 1
    return dict(sorted(counts.items()))


def main() -> None:
    source = resolve_source()
    items = collect_items(source)
    if not items:
        raise SystemExit(f"No importable Q&A found under {source}")

    payload = {
        "meta": {
            "version": 1,
            "count": len(items),
            "source_path": str(source),
            "source_label": "500_AI_QA",
            "tier": "advanced",
            "note": (
                "Imported from external corpus; not all 500 Readme outlines are "
                "implemented as structured Q&A yet. Re-run importer after upstream updates."
            ),
            "counts": category_counts(items),
        },
        "items": items,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )
    print(f"wrote {OUT_PATH} ({len(items)} items from {source})")
    print("counts:", payload["meta"]["counts"])


if __name__ == "__main__":
    main()
