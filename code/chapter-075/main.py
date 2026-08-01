#!/usr/bin/env python3
import json
from fwgraph import GraphEngine
def main():
    g=GraphEngine(start="a"); g.add_node("a", lambda s: {"v":1}); g.add_node("b", lambda s: {"v":s.get("v",0)+1}); g.add_edge("a","b"); g.add_edge("b","end"); print(json.dumps(g.run(), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
