"""Score portfolio projects and track OSS contributions."""
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
