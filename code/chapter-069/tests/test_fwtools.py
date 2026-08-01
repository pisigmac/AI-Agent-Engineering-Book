import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fwtools import default_registry
def test_call():
    r=default_registry(); assert r.call("add", {"a":1,"b":2})["result"]==3
def test_forbid():
    r=default_registry(); assert r.call("add", {"a":1,"b":2}, roles=("none",))["error"]=="forbidden"
