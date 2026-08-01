import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from costopt import CostOptimizer
def test_cache_and_route():
    o=CostOptimizer()
    a=o.complete("hello", task="simple"); b=o.complete("hello", task="simple")
    assert not a["cached"] and b["cached"] and b["cost_usd"]==0
    assert o.choose_model("complex multi-hop plan")=="large"
def test_budget():
    o=CostOptimizer(budget_usd=0.05)
    o.complete("a", task="complex plan"); r=o.complete("b", task="complex plan")
    assert "error" in r
