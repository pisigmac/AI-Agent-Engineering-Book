import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from statemachine import support_fsm
def test_happy_path():
    sm=support_fsm()
    sm.send("start"); sm.send("simple"); sm.send("done")
    assert sm.state=="completed"
def test_guard_escalate():
    sm=support_fsm()
    sm.send("start"); sm.send("simple")
    sm.send("escalate", {"confidence": 0.2})
    assert sm.state=="human"
