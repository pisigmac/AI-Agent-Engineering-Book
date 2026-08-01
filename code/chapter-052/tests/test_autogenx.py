import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autogenx.runtime import demo_chat
def test_chat():
    r = demo_chat().run("fix bug")
    assert r["ok"] and "TERMINATE" in r["final"]
