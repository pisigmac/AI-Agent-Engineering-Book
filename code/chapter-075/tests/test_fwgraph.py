import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fwgraph import GraphEngine
def test_graph():
    g=GraphEngine(start="a"); g.add_node("a", lambda s: {"x":1}); g.add_edge("a","end"); assert g.run()["x"]==1
