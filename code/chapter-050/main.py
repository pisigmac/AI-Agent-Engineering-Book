#!/usr/bin/env python3
import json
from langgraphx.runtime import demo_graph
def main():
    print(json.dumps(demo_graph().invoke({"text": "I need a refund"}), indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
