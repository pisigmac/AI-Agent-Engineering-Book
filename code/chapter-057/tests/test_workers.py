import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workers import JobQueue
def test_retry_then_success():
    state={"n":0}
    def h(p):
        if state["n"] < 1:
            state["n"]+=1; raise RuntimeError("x")
        return "ok"
    q=JobQueue(h); q.enqueue({})
    q.drain(); assert q.done and q.done[0]["ok"]
