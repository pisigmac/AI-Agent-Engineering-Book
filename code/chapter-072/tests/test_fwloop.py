import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fwloop import demo_loop
def test_loop():
    r=demo_loop().run("x"); assert r["ok"]
