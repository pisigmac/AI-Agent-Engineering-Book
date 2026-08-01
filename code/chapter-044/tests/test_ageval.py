import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ageval import evaluate, demo_agent, DEFAULT_CASES
def test_suite():
    r=evaluate(demo_agent, DEFAULT_CASES)
    assert r["pass_rate"] >= 0.9
