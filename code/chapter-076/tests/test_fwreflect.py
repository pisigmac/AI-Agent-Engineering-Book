import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fwreflect import ReflectionEngine
def test_critique():
    r=ReflectionEngine().critique("short", evidence="long evidence tokens here"); assert r["issues"]
