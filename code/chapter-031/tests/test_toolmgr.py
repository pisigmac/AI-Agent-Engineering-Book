import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from toolmgr import default_manager
def test_exec_ok():
    m=default_manager(); r=m.execute("get_weather", {"city":"Berlin"}); assert r["ok"] and "18C" in r["result"]
def test_permission_denied():
    m=default_manager(); r=m.execute("run_shell", {"cmd":"ls"}, roles=("default",)); assert not r["ok"] and r["error"]=="permission_denied"
def test_validation():
    m=default_manager(); r=m.execute("get_weather", {}); assert not r["ok"]
