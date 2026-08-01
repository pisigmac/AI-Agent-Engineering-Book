import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fwmemory import MemoryEngine
def test_memory():
    m=MemoryEngine(); m.add_turn("a"); m.remember("Berlin is cool"); assert m.search("Berlin")
