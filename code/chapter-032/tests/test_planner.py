import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from planner import Planner, PlanExecutor
def test_plan_execute():
    pl=Planner().plan("lookup weather", strategy="plan_execute")
    assert "call_tools" in pl.steps
def test_react():
    pl=Planner().plan("x", strategy="react"); assert pl.steps[0].startswith("thought")
def test_executor():
    r=PlanExecutor().run("research topic"); assert r["ok"] and r["trace"]
