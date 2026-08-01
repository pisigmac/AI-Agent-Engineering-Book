import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from crewx.runtime import demo_crew
def test_crew():
    r = demo_crew().kickoff({"topic": "RAG"})
    assert r["ok"] and len(r["outputs"])==2
