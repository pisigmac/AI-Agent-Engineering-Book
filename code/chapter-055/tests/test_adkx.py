import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adkx.runtime import demo_runner
def test_adk():
    r = demo_runner().run("u", "s", "search policies")
    assert r["ok"] and r["framework"]=="google_adk" and r["session"]["events"]
