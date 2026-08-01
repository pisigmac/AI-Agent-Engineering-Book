#!/usr/bin/env python3
import json
from fwplanner import Planner
def main():
    p=Planner(); plan=p.make("research agents"); print(json.dumps({"plan": plan.to_dict(), "replan": p.replan(plan, "empty results").to_dict()}, indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
