import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monkit import SLO, Monitor
def test_alert():
    s=SLO("x", 0.99)
    for _ in range(10): s.record(ok=False)
    assert Monitor([s]).evaluate()
