#!/usr/bin/env python3
"""
Export bootcamp interview bank (Ch 95) into the external 500_AI_QA project layout.

Writes into the target directory (default: ~/Documents/500_AI_QA):
  - bootcamp_interview_bank.yaml   — full structured export
  - bootcamp_interview_bank.py     — ai_questionnaire-compatible Python list
  - README_BOOTCAMP_EXPORT.md      — how this relates to the 500_AI_QA effort

IDs use range 9001–9784 (784 items) to avoid colliding with upstream 1–500 roadmap.

Env: INTERVIEW_500_AI_QA_PATH=/path/to/500_AI_QA
"""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path
from typing import Any

import yaml

SCRIPTS = Path(__file__).resolve().parents[1]
REPO_ROOT = SCRIPTS.parent
ID_BASE = 9001

CATEGORY_LABEL = {
    "python": "Python",
    "machine_learning": "Machine Learning",
    "system_design": "System Design",
    "ai_engineering": "AI Engineering",
    "generative_ai": "Generative AI",
    "prompt_engineering": "Prompt Engineering",
    "context_engineering": "Context Engineering",
    "loop_engineering": "Loop Engineering",
    "agent_frameworks": "Agent Frameworks",
    "agentic_ai": "Agentic AI",
    "behavioral": "Behavioral",
}


def resolve_target() -> Path:
    env = os.environ.get("INTERVIEW_500_AI_QA_PATH")
    if env:
        return Path(env).expanduser().resolve()
    for p in (
        Path.home() / "Documents" / "500_AI_QA",
        REPO_ROOT.parent / "500_AI_QA",
    ):
        if p.is_dir():
            return p
    return Path.home() / "Documents" / "500_AI_QA"


def load_bootcamp_items() -> list[dict[str, Any]]:
    import sys

    sys.path.insert(0, str(SCRIPTS))
    from interview_bank_data import load_bank_items

    return load_bank_items()


def _tagged_question(item: dict[str, Any]) -> str:
    cat = CATEGORY_LABEL.get(item.get("category", ""), item.get("category", "General"))
    diff = item.get("difficulty", "beginner")
    return f"[Bootcamp · {cat} · {diff}] {item['question']}"


def to_upstream_records(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        out.append(
            {
                "id": ID_BASE + i,
                "bootcamp_id": item.get("id"),
                "category": item.get("category"),
                "difficulty": item.get("difficulty", "beginner"),
                "tier": "beginner",
                "source": "ai_agent_engineering_bootcamp",
                "question": _tagged_question(item),
                "answer": item["answer"],
            }
        )
    return out


def write_yaml(target: Path, records: list[dict[str, Any]]) -> Path:
    path = target / "bootcamp_interview_bank.yaml"
    payload = {
        "meta": {
            "source_repo": "AI-Agent-Engineering-Bootcamp",
            "source_file": "scripts/data/interview_bank.yaml",
            "count": len(records),
            "id_range": [ID_BASE, ID_BASE + len(records) - 1],
            "tier": "beginner",
            "note": "Chapter 95 bank exported for merge into 500_AI_QA corpus.",
        },
        "items": records,
    }
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )
    return path


def _py_triple_string(s: str) -> str:
    """Pick a safe triple-quoted delimiter for Python source."""
    if '"""' not in s:
        return f'"""{s}"""'
    if "'''" not in s:
        return f"'''{s}'''"
    return json.dumps(s)


def write_python(target: Path, records: list[dict[str, Any]]) -> Path:
    path = target / "bootcamp_interview_bank.py"
    lines = [
        '"""',
        "Bootcamp Chapter 95 — interview Q&A exported from AI-Agent-Engineering-Bootcamp.",
        f"IDs {ID_BASE}–{ID_BASE + len(records) - 1} (beginner tier; does not replace 1–500 roadmap).",
        '"""',
        "",
        "bootcamp_questionnaire = [",
    ]
    for rec in records:
        q = rec["question"].replace("\\", "\\\\").replace('"', '\\"')
        a_block = _py_triple_string(rec["answer"])
        lines.append("    {")
        lines.append(f'        "id": {rec["id"]},')
        lines.append(f'        "category": "{rec["category"]}",')
        lines.append(f'        "bootcamp_id": "{rec["bootcamp_id"]}",')
        lines.append(f'        "question": "{q}",')
        lines.append(f'        "answer": {a_block},')
        lines.append("    },")
    lines.append("]")
    lines.append("")
    lines.append("# Alias for importers that expect this name:")
    lines.append("ai_questionnaire = bootcamp_questionnaire")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_readme(target: Path, records: list[dict[str, Any]], yaml_path: Path, py_path: Path) -> Path:
    path = target / "README_BOOTCAMP_EXPORT.md"
    counts: dict[str, int] = {}
    for r in records:
        c = r["category"]
        counts[c] = counts.get(c, 0) + 1
    body = textwrap.dedent(
        f"""\
        # Bootcamp export (Chapter 95)

        This folder's **500_AI_QA** project is the advanced/staff-engineering corpus.
        These files add the **beginner-friendly bootcamp bank** without overwriting `1.py` / `2.py`.

        | File | Contents |
        |------|----------|
        | `{yaml_path.name}` | {len(records)} Q&A (YAML) |
        | `{py_path.name}` | Same data as `bootcamp_questionnaire` / `ai_questionnaire` |

        - **ID range:** {ID_BASE}–{ID_BASE + len(records) - 1}
        - **Tier:** beginner (short answers; no heavy PyTorch by default)
        - **Regenerate:** from bootcamp repo:

        ```bash
        cd AI-Agent-Engineering-Bootcamp
        INTERVIEW_500_AI_QA_PATH="{target}" python3 scripts/interview_bank/export_to_500_ai_qa.py
        ```

        ## Category counts

        """
    )
    for cat, n in sorted(counts.items()):
        body += f"- `{cat}`: {n}\n"
    body += textwrap.dedent(
        """

        ## Suggested merge strategy

        1. Keep roadmap IDs **1–500** for advanced implementation Q&A (your original goal).
        2. Treat **9001+** as bootcamp foundation layer (interview prep for juniors / career switchers).
        3. Optional: concatenate lists in a master loader:

        ```python
        from bootcamp_interview_bank import bootcamp_questionnaire
        from complete_ai_questionnaire import complete_ai_questionnaire  # when valid

        all_qa = complete_ai_questionnaire + bootcamp_questionnaire
        ```
        """
    )
    path.write_text(body, encoding="utf-8")
    return path


def main() -> None:
    target = resolve_target()
    target.mkdir(parents=True, exist_ok=True)

    items = load_bootcamp_items()
    records = to_upstream_records(items)

    ypath = write_yaml(target, records)
    ppath = write_python(target, records)
    rpath = write_readme(target, records, ypath, ppath)

    print(f"target: {target}")
    print(f"wrote {ypath.name} ({len(records)} items)")
    print(f"wrote {ppath.name}")
    print(f"wrote {rpath.name}")


if __name__ == "__main__":
    main()
