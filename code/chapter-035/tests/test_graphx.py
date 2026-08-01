import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from graphx import research_graph
def test_graph_runs():
    r=research_graph().run({"goal": "RAG"})
    assert r.get("done") and "Report" in r.get("result","")
    assert r["checkpoints"]
