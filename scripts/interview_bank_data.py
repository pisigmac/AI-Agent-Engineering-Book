"""Load interview bank from canonical YAML (scripts/data/interview_bank.yaml)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CATEGORY_TITLES: dict[str, str] = {
    "python": "Python",
    "machine_learning": "Machine Learning",
    "system_design": "System Design",
    "ai_engineering": "AI Engineering & MLOps",
    "generative_ai": "Generative AI & LLMs",
    "prompt_engineering": "Prompt Engineering",
    "context_engineering": "Context Engineering",
    "loop_engineering": "Loop & Control Flow Engineering",
    "agent_frameworks": "Agent Frameworks (LangGraph, LangChain, CrewAI, n8n)",
    "agentic_ai": "Agentic AI",
    "behavioral": "Behavioral & Career",
}

MIN_PER_CATEGORY = 100

PREFIX_MAP = {
    "python": "py",
    "machine_learning": "ml",
    "system_design": "sd",
    "ai_engineering": "ae",
    "generative_ai": "ga",
    "prompt_engineering": "pe",
    "context_engineering": "cx",
    "loop_engineering": "lp",
    "agent_frameworks": "fw",
    "agentic_ai": "aa",
    "behavioral": "be",
}

# Canonical manuscript + tooling source (beginner, Chapter 95)
YAML_PATH = Path(__file__).resolve().parent / "data" / "interview_bank.yaml"

# Advanced corpus from external 500_AI_QA (scripts/interview_bank/import_500_ai_qa.py)
EXTERNAL_500_PATH = Path(__file__).resolve().parent / "data" / "interview_bank_500_ai_qa.yaml"

# Legacy pipe-delimited catalogs (used only by build_catalog.py export)
CATALOG_DIR = Path(__file__).resolve().parent / "interview_bank" / "catalog"
INTERMEDIATE_CATALOG_DIR = CATALOG_DIR / "intermediate"


def yaml_path() -> Path:
    return YAML_PATH


def _load_yaml() -> dict[str, Any]:
    if not YAML_PATH.is_file():
        raise FileNotFoundError(
            f"Missing {YAML_PATH}. Run:\n"
            "  python3 scripts/interview_bank/build_catalog.py\n"
            "  python3 scripts/interview_bank/export_yaml.py"
        )
    return yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))


def load_bank_items() -> list[dict[str, Any]]:
    data = _load_yaml()
    items = data.get("items") or []
    if not items:
        raise ValueError(f"No items in {YAML_PATH}")
    return items


def load_external_500_items() -> list[dict[str, Any]]:
    if not EXTERNAL_500_PATH.is_file():
        return []
    data = yaml.safe_load(EXTERNAL_500_PATH.read_text(encoding="utf-8"))
    return list(data.get("items") or [])


def load_combined_items(*, include_external: bool = True) -> list[dict[str, Any]]:
    items = load_bank_items()
    if include_external:
        items = items + load_external_500_items()
    return items


def category_counts(items: list[dict[str, Any]] | None = None) -> dict[str, int]:
    items = items if items is not None else load_bank_items()
    counts: dict[str, int] = {k: 0 for k in CATEGORY_TITLES}
    for item in items:
        cat = item.get("category", "")
        if cat in counts:
            counts[cat] += 1
    return counts


def assert_minimums(items: list[dict[str, Any]] | None = None) -> None:
    items = items if items is not None else load_bank_items()
    counts: dict[str, int] = {k: 0 for k in CATEGORY_TITLES}
    for item in items:
        if item.get("difficulty", "beginner") != "beginner":
            continue
        cat = item.get("category", "")
        if cat in counts:
            counts[cat] += 1
    bad = {k: v for k, v in counts.items() if v < MIN_PER_CATEGORY}
    if bad:
        raise ValueError(f"Categories below {MIN_PER_CATEGORY} beginner questions: {bad}")


def get_bank() -> list[dict[str, Any]]:
    """Load canonical bank and enforce per-category minimums."""
    items = load_bank_items()
    assert_minimums(items)
    return items
