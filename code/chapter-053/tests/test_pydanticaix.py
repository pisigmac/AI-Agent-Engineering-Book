import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pydanticaix.runtime import demo_agent, SupportDeps
def test_typed():
    r = demo_agent().run_sync("refund help", deps=SupportDeps(kb={"refund": "30 days"}))
    assert r["ok"] and r["data"]["intent"]=="billing" and r["data"]["confidence"] >= 0.9
