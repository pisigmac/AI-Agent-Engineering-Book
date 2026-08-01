import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tracekit import demo_trace, Tracer
def test_nested():
    exp=demo_trace(); assert len(exp["spans"])==3
    roots=[s for s in exp["spans"] if s["parent_id"] is None]
    assert len(roots)==1
