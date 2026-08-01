import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fwharness import Harness
def test_harness():
    def agent(g,c):
        return {"done": True, "result": "ok"} if c["step"]==1 else {}
    assert Harness(agent).run("g")["ok"]
