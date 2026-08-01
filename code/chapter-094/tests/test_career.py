import sys
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
