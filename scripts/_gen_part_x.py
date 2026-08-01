#!/usr/bin/env python3
"""Generate Part X — Career (chapters 91–94). Offline career tooling packages."""
from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = textwrap.dedent(content)
    if text.startswith("\n"):
        text = text[1:]
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text)


def pyproject(n: int) -> str:
    return f"""[project]
name = "ai-agent-platform-chapter-{n:03d}"
version = "1.0.0"
requires-python = ">=3.10"
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
"""


def readme(n: int, title: str, pkg: str) -> str:
    return f"""# Chapter {n:03d} — {title}

Career tooling package `{pkg}` (offline, no network).

```bash
cd code/chapter-{n:03d} && pytest -q && python3 main.py
```
"""


def book_md(
    n: int,
    title: str,
    pkg: str,
    overview: str,
    objectives: list[str],
    summary: str,
    next_line: str,
) -> str:
    objs = "\n".join(f"- {o}" for o in objectives)
    return f"""# Chapter {n}: {title}

## Chapter Overview

Part X **Career** — **{title}**.

{overview}

Package: `code/chapter-{n:03d}/{pkg}/`

## Learning Objectives

{objs}

## Prerequisites

Parts I–IX (platform, systems, framework, real projects).

## Motivation

Career outcomes require deliberate practice: system design fluency, interview readiness,
a public portfolio, and a personal roadmap. This chapter gives concrete tools—not slogans.

## Architecture

```text
code/chapter-{n:03d}/
  {pkg}/
  tests/
  main.py
  pyproject.toml
  README.md
```

## Internal Implementation

```bash
cd code/chapter-{n:03d} && pytest -q && python3 main.py
```

## Production Implementation

Use these modules as checklists in real interviews, design docs, GitHub READMEs, and quarterly planning.
Replace heuristic scorers with mentor feedback and production metrics over time.

## Mini Project

Run the chapter package end-to-end and adapt templates to your own target role or product.

## Visual diagrams

![Lifecycle](../diagrams/png/chapter-{n:03d}/lifecycle.png)

![Overview](../diagrams/png/chapter-{n:03d}/overview.png)

## Chapter Deliverables

| Artifact | Location |
|---|---|
| Manuscript | `book/chapter-{n:03d}.md` |
| Package | `code/chapter-{n:03d}/{pkg}/` |
| Tests | `code/chapter-{n:03d}/tests/` |

## Chapter Summary

{summary}

## What's Next

{next_line}
"""


def mermaid_pair(n: int, title: str, mid: str) -> None:
    d = ROOT / f"diagrams/mermaid/chapter-{n:03d}"
    write(
        d / "overview.mmd",
        f"""flowchart LR
  You[Reader] --> Tool[{title}]
  Tool --> Core[{mid}]
  Core --> Out[Artifacts]
""",
    )
    write(
        d / "lifecycle.mmd",
        f"""sequenceDiagram
  participant R as Reader
  participant T as {title}
  participant C as Core
  R->>T: input
  T->>C: evaluate
  C-->>T: score/report
  T-->>R: actionable output
""",
    )


def ch91() -> None:
    n, title, pkg = 91, "AI System Design", "sysdesign"
    base = ROOT / f"code/chapter-{n:03d}"
    write(base / "pyproject.toml", pyproject(n))
    write(base / "README.md", readme(n, title, pkg))
    write(
        base / f"{pkg}/__init__.py",
        '''"""AI system design helpers: capacity, latency budgets, design checklist."""
from .design import (
    CapacityEstimate,
    DesignChecklist,
    LatencyBudget,
    SystemDesignKit,
    estimate_capacity,
)

__all__ = [
    "CapacityEstimate",
    "DesignChecklist",
    "LatencyBudget",
    "SystemDesignKit",
    "estimate_capacity",
]
__version__ = "1.0.0"
''',
    )
    write(
        base / f"{pkg}/design.py",
        '''"""System design calculators and interview-style design scaffolding."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import math


@dataclass
class CapacityEstimate:
    qps: float
    daily_requests: float
    storage_gb_year: float
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "qps": round(self.qps, 3),
            "daily_requests": int(self.daily_requests),
            "storage_gb_year": round(self.storage_gb_year, 3),
            "notes": list(self.notes),
        }


def estimate_capacity(
    *,
    dau: int,
    requests_per_user_day: float,
    avg_payload_kb: float,
    retention_days: int = 365,
    peak_multiplier: float = 3.0,
) -> CapacityEstimate:
    """Back-of-envelope capacity for an AI product surface."""
    if dau < 0 or requests_per_user_day < 0 or avg_payload_kb < 0:
        raise ValueError("inputs must be non-negative")
    daily = dau * requests_per_user_day
    avg_qps = daily / 86_400.0
    peak_qps = avg_qps * peak_multiplier
    storage_gb = (daily * avg_payload_kb * retention_days) / (1024.0 * 1024.0)
    notes = [
        f"avg_qps={avg_qps:.3f}, design_for_peak_qps={peak_qps:.3f}",
        "Separate online inference path from batch/index rebuild jobs",
        "Budget LLM tokens separately from request QPS",
    ]
    return CapacityEstimate(
        qps=peak_qps,
        daily_requests=daily,
        storage_gb_year=storage_gb,
        notes=notes,
    )


@dataclass
class LatencyBudget:
    """Milliseconds budget breakdown for an agent request path."""

    total_ms: int
    parts: dict[str, int]  # name -> ms

    def remaining(self) -> int:
        return self.total_ms - sum(self.parts.values())

    def valid(self) -> bool:
        return self.remaining() >= 0 and all(v >= 0 for v in self.parts.values())

    def as_dict(self) -> dict[str, Any]:
        return {
            "total_ms": self.total_ms,
            "parts": dict(self.parts),
            "remaining_ms": self.remaining(),
            "valid": self.valid(),
        }


DEFAULT_CHECKLIST = [
    "Clarify requirements and non-goals",
    "Estimate scale (QPS, storage, cost)",
    "Draw high-level architecture",
    "Deep-dive critical path (RAG / tools / multi-agent)",
    "Data model and consistency",
    "Failure modes and retries",
    "Observability and evaluation gates",
    "Security, tenancy, and abuse",
    "Cost and model routing",
    "Rollout, canaries, and rollback",
]


@dataclass
class DesignChecklist:
    items: list[str] = field(default_factory=lambda: list(DEFAULT_CHECKLIST))
    done: set[str] = field(default_factory=set)

    def mark(self, item: str) -> None:
        if item not in self.items:
            raise KeyError(item)
        self.done.add(item)

    def progress(self) -> dict[str, Any]:
        return {
            "total": len(self.items),
            "done": len(self.done),
            "pct": round(100.0 * len(self.done) / max(1, len(self.items)), 1),
            "remaining": [i for i in self.items if i not in self.done],
        }


@dataclass
class SystemDesignKit:
    """Compose capacity + latency + checklist into a design brief."""

    title: str
    checklist: DesignChecklist = field(default_factory=DesignChecklist)

    def brief(
        self,
        *,
        dau: int,
        requests_per_user_day: float,
        avg_payload_kb: float,
        latency: LatencyBudget,
    ) -> dict[str, Any]:
        cap = estimate_capacity(
            dau=dau,
            requests_per_user_day=requests_per_user_day,
            avg_payload_kb=avg_payload_kb,
        )
        return {
            "title": self.title,
            "capacity": cap.as_dict(),
            "latency": latency.as_dict(),
            "checklist": self.checklist.progress(),
            "components_hint": [
                "API gateway + auth",
                "Orchestrator / agent loop",
                "Tool adapters",
                "Vector/index store",
                "LLM gateway with budgets",
                "Eval + observability",
            ],
        }
''',
    )
    write(
        base / "main.py",
        '''#!/usr/bin/env python3
import json
from sysdesign import SystemDesignKit, LatencyBudget


def main() -> int:
    kit = SystemDesignKit(title="Multi-tenant support agent")
    kit.checklist.mark("Clarify requirements and non-goals")
    kit.checklist.mark("Estimate scale (QPS, storage, cost)")
    budget = LatencyBudget(
        total_ms=3000,
        parts={"auth": 50, "retrieve": 200, "llm": 2000, "tools": 400, "post": 50},
    )
    print(json.dumps(kit.brief(
        dau=100_000,
        requests_per_user_day=2.0,
        avg_payload_kb=4.0,
        latency=budget,
    ), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    )
    write(
        base / "tests/test_sysdesign.py",
        '''import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sysdesign import estimate_capacity, LatencyBudget, DesignChecklist, SystemDesignKit


def test_capacity():
    c = estimate_capacity(dau=86_400, requests_per_user_day=1.0, avg_payload_kb=1.0, peak_multiplier=1.0)
    assert c.daily_requests == 86_400
    assert abs(c.qps - 1.0) < 1e-6


def test_latency_budget():
    b = LatencyBudget(total_ms=1000, parts={"a": 400, "b": 500})
    assert b.remaining() == 100
    assert b.valid()
    bad = LatencyBudget(total_ms=100, parts={"a": 80, "b": 30})
    assert not bad.valid()


def test_checklist_and_brief():
    kit = SystemDesignKit(title="X")
    kit.checklist.mark(kit.checklist.items[0])
    out = kit.brief(
        dau=1000,
        requests_per_user_day=1,
        avg_payload_kb=1,
        latency=LatencyBudget(1000, {"llm": 800}),
    )
    assert out["checklist"]["done"] == 1
    assert "capacity" in out


def test_negative():
    with pytest.raises(ValueError):
        estimate_capacity(dau=-1, requests_per_user_day=1, avg_payload_kb=1)
''',
    )
    write(
        ROOT / f"book/chapter-{n:03d}.md",
        book_md(
            n,
            title,
            pkg,
            "Practice AI system design with capacity estimates, latency budgets, and a production checklist.",
            [
                "Estimate QPS, storage, and peak load for AI products",
                "Allocate end-to-end latency budgets across retrieve / LLM / tools",
                "Walk a 10-point system design interview checklist",
                "Produce a structured design brief for an agent system",
            ],
            "AI System Design kit turns vague interview prompts into quantified architecture briefs.",
            "**Chapter 92** covers technical interview practice loops and rubrics.",
        ),
    )
    mermaid_pair(n, title, "CapacityLatency")


def ch92() -> None:
    n, title, pkg = 92, "Technical Interviews", "interview"
    base = ROOT / f"code/chapter-{n:03d}"
    write(base / "pyproject.toml", pyproject(n))
    write(base / "README.md", readme(n, title, pkg))
    write(
        base / f"{pkg}/__init__.py",
        '''"""Technical interview bank, rubrics, and mock session runner."""
from .prep import Question, Rubric, MockInterview, InterviewBank, score_answer

__all__ = ["Question", "Rubric", "MockInterview", "InterviewBank", "score_answer"]
__version__ = "1.0.0"
''',
    )
    write(
        base / f"{pkg}/prep.py",
        '''"""Interview question bank and lightweight answer scoring."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re


@dataclass
class Question:
    id: str
    category: str  # coding | system_design | agents | behavioral
    prompt: str
    keywords: list[str]
    difficulty: str = "medium"  # easy|medium|hard


@dataclass
class Rubric:
    """Keyword coverage + structure signals (not a real LLM judge)."""

    min_keywords: int = 2
    require_structure: bool = True  # look for numbered/sections signals

    def structure_ok(self, answer: str) -> bool:
        if not self.require_structure:
            return True
        if re.search(r"(?m)^\\s*(\\d+[.)]|[-*])\\s+", answer):
            return True
        return any(
            h in answer.lower()
            for h in ("first", "second", "trade-off", "tradeoff", "in summary", "approach")
        )


def score_answer(question: Question, answer: str, rubric: Rubric | None = None) -> dict[str, Any]:
    rubric = rubric or Rubric()
    text = answer.lower()
    hits = [k for k in question.keywords if k.lower() in text]
    kw_score = len(hits) / max(1, len(question.keywords))
    struct = rubric.structure_ok(answer)
    length_ok = len(answer.strip()) >= 40
    passed = len(hits) >= rubric.min_keywords and struct and length_ok
    return {
        "question_id": question.id,
        "keyword_hits": hits,
        "keyword_score": round(kw_score, 3),
        "structure_ok": struct,
        "length_ok": length_ok,
        "passed": passed,
        "feedback": _feedback(hits, struct, length_ok, question),
    }


def _feedback(hits: list[str], struct: bool, length_ok: bool, q: Question) -> list[str]:
    tips: list[str] = []
    missing = [k for k in q.keywords if k not in hits]
    if missing:
        tips.append(f"Mention concepts: {', '.join(missing[:5])}")
    if not struct:
        tips.append("Structure the answer (steps, trade-offs, summary)")
    if not length_ok:
        tips.append("Expand with a concrete example or numbers")
    if not tips:
        tips.append("Solid coverage — deepen with failure modes or metrics")
    return tips


DEFAULT_BANK: list[Question] = [
    Question(
        "sd1",
        "system_design",
        "Design a multi-tenant RAG support agent.",
        ["retrieval", "tenancy", "evaluation", "latency", "cost"],
        "hard",
    ),
    Question(
        "ag1",
        "agents",
        "How do you prevent tool-calling agents from taking unsafe actions?",
        ["allowlist", "human-in-the-loop", "sandbox", "policy", "audit"],
        "medium",
    ),
    Question(
        "co1",
        "coding",
        "Implement a retry with exponential backoff.",
        ["retry", "backoff", "jitter", "idempotent", "timeout"],
        "easy",
    ),
    Question(
        "be1",
        "behavioral",
        "Tell me about a production incident you led.",
        ["impact", "root cause", "timeline", "fix", "prevention"],
        "medium",
    ),
]


@dataclass
class InterviewBank:
    questions: list[Question] = field(default_factory=lambda: list(DEFAULT_BANK))

    def by_category(self, category: str) -> list[Question]:
        return [q for q in self.questions if q.category == category]

    def get(self, qid: str) -> Question:
        for q in self.questions:
            if q.id == qid:
                return q
        raise KeyError(qid)


@dataclass
class MockInterview:
    bank: InterviewBank
    rubric: Rubric = field(default_factory=Rubric)
    results: list[dict[str, Any]] = field(default_factory=list)

    def ask(self, qid: str, answer: str) -> dict[str, Any]:
        q = self.bank.get(qid)
        result = score_answer(q, answer, self.rubric)
        self.results.append(result)
        return result

    def summary(self) -> dict[str, Any]:
        if not self.results:
            return {"n": 0, "pass_rate": 0.0, "results": []}
        passed = sum(1 for r in self.results if r["passed"])
        return {
            "n": len(self.results),
            "pass_rate": round(passed / len(self.results), 3),
            "results": list(self.results),
        }
''',
    )
    write(
        base / "main.py",
        '''#!/usr/bin/env python3
import json
from interview import InterviewBank, MockInterview


def main() -> int:
    mock = MockInterview(bank=InterviewBank())
    mock.ask(
        "ag1",
        "First, allowlist tools. Second, sandbox side effects. "
        "Add human-in-the-loop for risky actions, policy checks, and an audit log.",
    )
    mock.ask(
        "co1",
        "Use retry with exponential backoff and jitter; keep calls idempotent; set timeouts.",
    )
    print(json.dumps(mock.summary(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    )
    write(
        base / "tests/test_interview.py",
        '''import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from interview import InterviewBank, MockInterview, score_answer


def test_score_pass():
    q = InterviewBank().get("ag1")
    r = score_answer(
        q,
        "First, use an allowlist and sandbox execution. Second, require "
        "human-in-the-loop approval with policy gates and a full audit trail.",
    )
    assert r["passed"] is True


def test_score_fail_short():
    q = InterviewBank().get("ag1")
    r = score_answer(q, "be careful")
    assert r["passed"] is False


def test_mock_summary():
    m = MockInterview(bank=InterviewBank())
    m.ask("be1", "Impact was outage. Root cause was bad deploy. Timeline 30m. Fix rollback. Prevention canary.")
    s = m.summary()
    assert s["n"] == 1
    assert 0 <= s["pass_rate"] <= 1
''',
    )
    write(
        ROOT / f"book/chapter-{n:03d}.md",
        book_md(
            n,
            title,
            pkg,
            "Run mock technical interviews with a question bank, keyword rubrics, and pass/fail feedback.",
            [
                "Practice system design, agents, coding, and behavioral prompts",
                "Score answers with keyword + structure rubrics",
                "Track mock session pass rates",
                "Turn feedback into study loops",
            ],
            "Technical Interviews package provides a repeatable offline mock-interview loop.",
            "**Chapter 93** builds portfolio and open-source contribution trackers.",
        ),
    )
    mermaid_pair(n, title, "MockRubric")


def ch93() -> None:
    n, title, pkg = 93, "Portfolio & Open Source", "portfolio"
    base = ROOT / f"code/chapter-{n:03d}"
    write(base / "pyproject.toml", pyproject(n))
    write(base / "README.md", readme(n, title, pkg))
    write(
        base / f"{pkg}/__init__.py",
        '''"""Portfolio project scorer and open-source contribution tracker."""
from .folio import Project, Portfolio, Contribution, score_project, README_CHECKS

__all__ = ["Project", "Portfolio", "Contribution", "score_project", "README_CHECKS"]
__version__ = "1.0.0"
''',
    )
    write(
        base / f"{pkg}/folio.py",
        '''"""Score portfolio projects and track OSS contributions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


README_CHECKS = [
    "problem_statement",
    "architecture_diagram",
    "quickstart",
    "tests",
    "license",
    "demo_or_screenshots",
]


@dataclass
class Project:
    name: str
    url: str
    tags: list[str] = field(default_factory=list)
    readme_flags: dict[str, bool] = field(default_factory=dict)
    has_tests: bool = False
    has_ci: bool = False
    has_docker: bool = False
    stars: int = 0
    production_used: bool = False


def score_project(p: Project) -> dict[str, Any]:
    """Heuristic 0–100 portfolio quality score."""
    points = 0
    max_points = 0
    details: list[str] = []

    def add(label: str, got: bool, weight: int) -> None:
        nonlocal points, max_points
        max_points += weight
        if got:
            points += weight
            details.append(f"+{weight} {label}")
        else:
            details.append(f"+0 {label} (missing)")

    for key in README_CHECKS:
        add(f"readme:{key}", bool(p.readme_flags.get(key)), 8)
    add("tests", p.has_tests, 12)
    add("ci", p.has_ci, 10)
    add("docker", p.has_docker, 8)
    add("production_used", p.production_used, 10)
    # stars soft signal capped
    star_pts = min(10, p.stars // 5)
    points += star_pts
    max_points += 10
    details.append(f"+{star_pts} stars_signal")

    pct = round(100.0 * points / max_points, 1) if max_points else 0.0
    grade = "A" if pct >= 85 else "B" if pct >= 70 else "C" if pct >= 55 else "D"
    return {
        "name": p.name,
        "score": pct,
        "grade": grade,
        "points": points,
        "max_points": max_points,
        "details": details,
        "gaps": [d for d in details if d.startswith("+0")],
    }


@dataclass
class Contribution:
    repo: str
    kind: str  # pr|issue|docs|talk
    title: str
    url: str = ""
    merged: bool = False


@dataclass
class Portfolio:
    projects: list[Project] = field(default_factory=list)
    contributions: list[Contribution] = field(default_factory=list)

    def add_project(self, p: Project) -> None:
        self.projects.append(p)

    def add_contribution(self, c: Contribution) -> None:
        self.contributions.append(c)

    def report(self) -> dict[str, Any]:
        scored = [score_project(p) for p in self.projects]
        avg = round(sum(s["score"] for s in scored) / len(scored), 1) if scored else 0.0
        merged = sum(1 for c in self.contributions if c.merged)
        return {
            "n_projects": len(self.projects),
            "avg_score": avg,
            "projects": scored,
            "contributions": [
                {
                    "repo": c.repo,
                    "kind": c.kind,
                    "title": c.title,
                    "merged": c.merged,
                }
                for c in self.contributions
            ],
            "merged_contributions": merged,
            "recommendations": _recs(scored, self.contributions),
        }


def _recs(scored: list[dict[str, Any]], contribs: list[Contribution]) -> list[str]:
    recs: list[str] = []
    if not scored:
        recs.append("Publish at least 2–3 polished agent projects with tests and CI")
    for s in scored:
        if s["grade"] in {"C", "D"}:
            recs.append(f"Improve {s['name']}: {', '.join(s['gaps'][:3]) or 'polish README'}")
    if not any(c.kind == "docs" for c in contribs):
        recs.append("Land a docs PR on a framework you use daily")
    if not any(c.merged for c in contribs):
        recs.append("Aim for one merged OSS PR this month")
    if not recs:
        recs.append("Portfolio looks strong — add a public write-up / demo video")
    return recs
''',
    )
    write(
        base / "main.py",
        '''#!/usr/bin/env python3
import json
from portfolio import Project, Portfolio, Contribution


def main() -> int:
    folio = Portfolio()
    folio.add_project(
        Project(
            name="support-agent",
            url="https://github.com/you/support-agent",
            tags=["agents", "rag"],
            readme_flags={k: True for k in [
                "problem_statement", "architecture_diagram", "quickstart", "tests", "license", "demo_or_screenshots"
            ]},
            has_tests=True,
            has_ci=True,
            has_docker=True,
            stars=12,
            production_used=False,
        )
    )
    folio.add_project(
        Project(
            name="toy-bot",
            url="https://github.com/you/toy-bot",
            readme_flags={"quickstart": True},
            has_tests=False,
        )
    )
    folio.add_contribution(Contribution("langchain", "docs", "Fix tool calling example", merged=True))
    print(json.dumps(folio.report(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    )
    write(
        base / "tests/test_portfolio.py",
        '''import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from portfolio import Project, Portfolio, Contribution, score_project, README_CHECKS


def test_score_strong_project():
    p = Project(
        name="x",
        url="u",
        readme_flags={k: True for k in README_CHECKS},
        has_tests=True,
        has_ci=True,
        has_docker=True,
        stars=50,
        production_used=True,
    )
    s = score_project(p)
    assert s["score"] >= 85
    assert s["grade"] == "A"


def test_portfolio_recs():
    folio = Portfolio()
    folio.add_project(Project(name="weak", url="u"))
    r = folio.report()
    assert r["n_projects"] == 1
    assert r["recommendations"]
''',
    )
    write(
        ROOT / f"book/chapter-{n:03d}.md",
        book_md(
            n,
            title,
            pkg,
            "Score GitHub portfolio projects against hiring-friendly checklists and track OSS contributions.",
            [
                "Apply a README / tests / CI / Docker quality rubric",
                "Grade projects A–D with actionable gaps",
                "Log open-source contributions and merged PRs",
                "Generate portfolio improvement recommendations",
            ],
            "Portfolio & Open Source tooling turns vague 'build in public' advice into measurable scores.",
            "**Chapter 94** closes the book with a career roadmap and startup guide.",
        ),
    )
    mermaid_pair(n, title, "ScoreTrack")


def ch94() -> None:
    n, title, pkg = 94, "Career Roadmap & Startup Guide", "career"
    base = ROOT / f"code/chapter-{n:03d}"
    write(base / "pyproject.toml", pyproject(n))
    write(base / "README.md", readme(n, title, pkg))
    write(
        base / f"{pkg}/__init__.py",
        '''"""Career roadmap milestones and lean startup canvas helper."""
from .roadmap import (
    Milestone,
    Roadmap,
    Skill,
    SkillGraph,
    LeanCanvas,
    StartupGuide,
)

__all__ = [
    "Milestone",
    "Roadmap",
    "Skill",
    "SkillGraph",
    "LeanCanvas",
    "StartupGuide",
]
__version__ = "1.0.0"
''',
    )
    write(
        base / f"{pkg}/roadmap.py",
        '''"""Quarterly roadmap, skill graph, and lean canvas for AI careers/startups."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Skill:
    name: str
    level: int = 0  # 0-5
    target: int = 3
    tags: list[str] = field(default_factory=list)

    @property
    def gap(self) -> int:
        return max(0, self.target - self.level)


@dataclass
class SkillGraph:
    skills: list[Skill] = field(default_factory=list)

    def add(self, skill: Skill) -> None:
        self.skills.append(skill)

    def gaps(self) -> list[dict[str, Any]]:
        rows = [
            {"name": s.name, "level": s.level, "target": s.target, "gap": s.gap, "tags": s.tags}
            for s in self.skills
            if s.gap > 0
        ]
        rows.sort(key=lambda r: r["gap"], reverse=True)
        return rows

    def readiness_pct(self) -> float:
        if not self.skills:
            return 0.0
        total_t = sum(s.target for s in self.skills) or 1
        total_l = sum(min(s.level, s.target) for s in self.skills)
        return round(100.0 * total_l / total_t, 1)


@dataclass
class Milestone:
    id: str
    title: str
    quarter: str  # e.g. 2026-Q3
    done: bool = False
    kind: str = "career"  # career|learning|startup|oss


@dataclass
class Roadmap:
    milestones: list[Milestone] = field(default_factory=list)

    def add(self, m: Milestone) -> None:
        self.milestones.append(m)

    def complete(self, mid: str) -> None:
        for m in self.milestones:
            if m.id == mid:
                m.done = True
                return
        raise KeyError(mid)

    def progress(self) -> dict[str, Any]:
        n = len(self.milestones)
        done = sum(1 for m in self.milestones if m.done)
        by_q: dict[str, list[dict[str, Any]]] = {}
        for m in self.milestones:
            by_q.setdefault(m.quarter, []).append(
                {"id": m.id, "title": m.title, "done": m.done, "kind": m.kind}
            )
        return {
            "total": n,
            "done": done,
            "pct": round(100.0 * done / n, 1) if n else 0.0,
            "by_quarter": by_q,
        }


@dataclass
class LeanCanvas:
    """One-page lean canvas for an AI product idea."""

    problem: list[str] = field(default_factory=list)
    customer_segments: list[str] = field(default_factory=list)
    unique_value: str = ""
    solution: list[str] = field(default_factory=list)
    channels: list[str] = field(default_factory=list)
    revenue: list[str] = field(default_factory=list)
    cost_structure: list[str] = field(default_factory=list)
    key_metrics: list[str] = field(default_factory=list)
    unfair_advantage: str = ""

    def completeness(self) -> dict[str, Any]:
        fields = {
            "problem": bool(self.problem),
            "customer_segments": bool(self.customer_segments),
            "unique_value": bool(self.unique_value.strip()),
            "solution": bool(self.solution),
            "channels": bool(self.channels),
            "revenue": bool(self.revenue),
            "cost_structure": bool(self.cost_structure),
            "key_metrics": bool(self.key_metrics),
            "unfair_advantage": bool(self.unfair_advantage.strip()),
        }
        filled = sum(1 for v in fields.values() if v)
        return {
            "filled": filled,
            "total": len(fields),
            "pct": round(100.0 * filled / len(fields), 1),
            "missing": [k for k, v in fields.items() if not v],
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "problem": list(self.problem),
            "customer_segments": list(self.customer_segments),
            "unique_value": self.unique_value,
            "solution": list(self.solution),
            "channels": list(self.channels),
            "revenue": list(self.revenue),
            "cost_structure": list(self.cost_structure),
            "key_metrics": list(self.key_metrics),
            "unfair_advantage": self.unfair_advantage,
            "completeness": self.completeness(),
        }


DEFAULT_SKILLS = [
    Skill("Python engineering", level=3, target=4, tags=["core"]),
    Skill("Agent orchestration", level=2, target=4, tags=["agents"]),
    Skill("RAG & retrieval", level=2, target=4, tags=["rag"]),
    Skill("Evaluation harnesses", level=1, target=4, tags=["quality"]),
    Skill("Production APIs", level=2, target=3, tags=["backend"]),
    Skill("System design interviews", level=1, target=3, tags=["career"]),
    Skill("Open source presence", level=1, target=3, tags=["career"]),
]


@dataclass
class StartupGuide:
    skills: SkillGraph = field(default_factory=SkillGraph)
    roadmap: Roadmap = field(default_factory=Roadmap)
    canvas: LeanCanvas = field(default_factory=LeanCanvas)

    @classmethod
    def default_track(cls) -> "StartupGuide":
        g = cls()
        for s in DEFAULT_SKILLS:
            g.skills.add(Skill(s.name, s.level, s.target, list(s.tags)))
        g.roadmap.add(Milestone("m1", "Ship portfolio agent with CI", "2026-Q3", kind="career"))
        g.roadmap.add(Milestone("m2", "Pass 10 mock system designs", "2026-Q3", kind="learning"))
        g.roadmap.add(Milestone("m3", "Merged OSS PR", "2026-Q3", kind="oss"))
        g.roadmap.add(Milestone("m4", "Interview loop / offer", "2026-Q4", kind="career"))
        g.roadmap.add(Milestone("m5", "Validate AI product wedge (10 users)", "2026-Q4", kind="startup"))
        return g

    def snapshot(self) -> dict[str, Any]:
        return {
            "skill_readiness_pct": self.skills.readiness_pct(),
            "skill_gaps": self.skills.gaps()[:5],
            "roadmap": self.roadmap.progress(),
            "canvas": self.canvas.as_dict(),
            "next_actions": self._next_actions(),
        }

    def _next_actions(self) -> list[str]:
        actions: list[str] = []
        gaps = self.skills.gaps()
        if gaps:
            actions.append(f"Level up skill: {gaps[0]['name']} (gap {gaps[0]['gap']})")
        for m in self.roadmap.milestones:
            if not m.done:
                actions.append(f"Milestone: {m.title} ({m.quarter})")
                break
        miss = self.canvas.completeness()["missing"]
        if miss:
            actions.append(f"Fill lean canvas field: {miss[0]}")
        if not actions:
            actions.append("Review quarterly goals and raise skill targets")
        return actions
''',
    )
    write(
        base / "main.py",
        '''#!/usr/bin/env python3
import json
from career import StartupGuide


def main() -> int:
    guide = StartupGuide.default_track()
    guide.canvas.problem = ["Support tickets overwhelm SMBs"]
    guide.canvas.customer_segments = ["B2B SaaS under 200 employees"]
    guide.canvas.unique_value = "Agent that resolves L1 with eval gates"
    guide.canvas.solution = ["KB RAG", "ticket tools", "escalation policy"]
    guide.canvas.key_metrics = ["resolution rate", "cost per ticket"]
    guide.roadmap.complete("m1")
    print(json.dumps(guide.snapshot(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    )
    write(
        base / "tests/test_career.py",
        '''import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from career import StartupGuide, Skill, SkillGraph, LeanCanvas, Roadmap, Milestone


def test_default_snapshot():
    g = StartupGuide.default_track()
    s = g.snapshot()
    assert s["skill_readiness_pct"] > 0
    assert s["roadmap"]["total"] >= 4
    assert s["next_actions"]


def test_skill_gaps():
    sg = SkillGraph()
    sg.add(Skill("x", level=1, target=4))
    sg.add(Skill("y", level=3, target=3))
    gaps = sg.gaps()
    assert len(gaps) == 1
    assert gaps[0]["name"] == "x"


def test_canvas_and_roadmap():
    c = LeanCanvas(problem=["p"], unique_value="v")
    assert "customer_segments" in c.completeness()["missing"]
    r = Roadmap()
    r.add(Milestone("a", "A", "2026-Q3"))
    r.complete("a")
    assert r.progress()["done"] == 1
    with pytest.raises(KeyError):
        r.complete("nope")
''',
    )
    write(
        ROOT / f"book/chapter-{n:03d}.md",
        book_md(
            n,
            title,
            pkg,
            "Close the bootcamp with a skill graph, quarterly milestones, and a lean canvas for AI products.",
            [
                "Map skill levels vs targets for AI agent engineering roles",
                "Track quarterly career, learning, OSS, and startup milestones",
                "Fill a lean canvas for an AI product wedge",
                "Generate prioritized next actions from gaps",
            ],
            "Career Roadmap & Startup Guide gives a living plan after the bootcamp ends.",
            "You finished the **AI Agent Engineering Bootcamp (2026 Edition)** — keep shipping, measuring, and teaching others.",
        ),
    )
    mermaid_pair(n, title, "SkillsMilestones")


def main() -> None:
    ch91()
    ch92()
    ch93()
    ch94()
    readme_path = ROOT / "README.md"
    text = readme_path.read_text()
    old = "Manuscript and code slices currently include chapters **1–90** (through Part IX Real Projects). Next: Part X — Career (91–94)."
    new = "Manuscript and code slices currently include chapters **1–94** (full curriculum: Parts I–X complete)."
    if old in text:
        readme_path.write_text(text.replace(old, new))
    else:
        # fallback patterns
        import re

        text2, n = re.subn(
            r"Manuscript and code slices currently include chapters \*\*1–\d+\*\*.*",
            new,
            text,
            count=1,
        )
        if n:
            readme_path.write_text(text2)
    print("Part X chapters 91–94 generated.")


if __name__ == "__main__":
    main()
