import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from harness import AgentHarness, Budget, demo_agent
def test_success():
    r=AgentHarness(demo_agent, budget=Budget(max_steps=5)).run("weather")
    assert r["ok"] and r["result"]
def test_budget():
    def spend(g,c): return {"cost_usd": 1.0}
    r=AgentHarness(spend, budget=Budget(max_steps=5, max_cost_usd=0.5)).run("x")
    assert not r["ok"]
