import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cicdkit import Pipeline, Step, demo_pipeline
def test_pass():
    assert demo_pipeline().run()["ok"]
def test_gate_fail():
    p=Pipeline("t"); p.add(Step("x", lambda: {"ok": False}, gate=True)); assert not p.run()["ok"]
