import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from multiagent import research_assistant
def test_research_flow():
    r=research_assistant().run("vector databases")
    assert r["ok"] and r["final"] and r["trace"]
    roles=[t["role"] for t in r["trace"]]
    assert roles[0]=="planner" and "reviewer" in roles
