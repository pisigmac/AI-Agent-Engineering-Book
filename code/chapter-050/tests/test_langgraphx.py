import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from langgraphx.runtime import demo_graph
def test_graph():
    r = demo_graph().invoke({"text": "refund please"})
    assert r["ok"] and r["intent"]=="billing" and "30" in r["result"]
