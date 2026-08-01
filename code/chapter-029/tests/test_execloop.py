import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from execloop import default_engine, ExecutionEngine

def test_weather_loop():
    r = default_engine().run("get weather")
    assert r["ok"] and r["reason"] in {"done", "terminate"}

def test_retry_exhaustion():
    def decide(g, h):
        return {"action": {"name": "bad"}}
    def act(a):
        return {"ok": False, "error": "x"}
    r = ExecutionEngine(decide, act, max_steps=5, max_retries=1).run("x")
    assert not r["ok"] and r["reason"] == "max_retries"
