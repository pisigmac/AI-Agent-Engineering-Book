import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from observ import traced_agent_run, Telemetry
def test_trace():
    r=traced_agent_run("x"); assert r["telemetry"]["traces"] and r["telemetry"]["metrics"]["span.count"]>=2
def test_error_span():
    t=Telemetry()
    try:
        with t.span("boom"):
            raise RuntimeError("x")
    except RuntimeError:
        pass
    assert t.spans[0].status=="error"
