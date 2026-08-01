import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eventbus import EventBus, demo_ticket_flow
def test_pubsub():
    r=demo_ticket_flow(); assert any(h.startswith("triage:") for h in r["handled"])
def test_consume_queue():
    b=EventBus(); b.publish("a", {"x":1}); assert b.consume("a")[0]["x"]==1
