import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fwplanner import Planner
def test_plan_replan():
    p=Planner(); plan=p.make("find docs"); assert "search" in plan.steps
    r=p.replan(plan, "fail"); assert r.version==2
