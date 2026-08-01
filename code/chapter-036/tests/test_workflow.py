import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workflow import Workflow, Step, demo_workflow
def test_demo():
    r=demo_workflow().run({"text":"refund please"}); assert r["ok"] and "answer" in r["context"]
def test_retry_fail():
    n={"i":0}
    def boom(c):
        n["i"]+=1; raise RuntimeError("x")
    wf=Workflow("t"); wf.add(Step("x", boom, retries=1))
    r=wf.run({}); assert not r["ok"] and n["i"]==2
