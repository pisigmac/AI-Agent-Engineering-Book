import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fweval import Evaluator, Example, exact_scorer
def test_gate():
    ev=Evaluator(exact_scorer, gate=1.0)
    r=ev.evaluate(lambda x: x, [Example("1","a","a")]); assert r["pass"]
