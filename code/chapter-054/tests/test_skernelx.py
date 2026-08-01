import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skernelx.runtime import demo_kernel
def test_kernel():
    r = demo_kernel().run_plan("weather")
    assert r["ok"] and "18C" in r["result"]
