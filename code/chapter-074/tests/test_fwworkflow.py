import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fwworkflow import WorkflowEngine, Step
def test_ok():
    w=WorkflowEngine(); w.add(Step("a", lambda s: {"v":1})); assert w.run()["ok"]
def test_retry():
    n={"i":0}
    def f(s):
        n["i"]+=1
        if n["i"]<2: raise RuntimeError("x")
        return {"done":1}
    w=WorkflowEngine(); w.add(Step("r", f, retries=2)); assert w.run()["ok"]
