import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reflect import ReflectionEngine
def test_ok_answer():
    r=ReflectionEngine().reflect("Refunds are available within 30 days for unused products.", evidence="Refunds within 30 days")
    assert r.confidence >= 0.5
def test_empty():
    r=ReflectionEngine().reflect("")
    assert not r.accepted and r.confidence == 0.0
