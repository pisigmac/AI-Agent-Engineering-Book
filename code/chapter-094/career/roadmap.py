"""Quarterly roadmap, skill graph, and lean canvas for AI careers/startups."""
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
