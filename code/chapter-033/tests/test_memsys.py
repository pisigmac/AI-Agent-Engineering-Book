import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from memsys import MemorySystem
def test_memory_layers():
    m=MemorySystem(); m.remember_turn("hi","hello"); m.remember_fact("Berlin timezone CET")
    ctx=m.context("Berlin")
    assert ctx["working"] and ctx["episodic"] and ctx["semantic"]
