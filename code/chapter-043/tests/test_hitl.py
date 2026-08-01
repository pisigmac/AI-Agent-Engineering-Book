import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hitl import HITLController
def test_low_auto():
    c=HITLController(); r=c.run_action("log", {}, risk="low"); assert r["ok"]
def test_high_interrupt_then_approve():
    c=HITLController(); r=c.run_action("refund", {"x":1}, risk="high"); assert r["interrupted"]
    rid=r["request_id"]; c.approve(rid); assert rid not in c.pending
