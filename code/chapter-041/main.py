#!/usr/bin/env python3
import json
from statemachine import support_fsm
def main():
    sm=support_fsm()
    for ev,ctx in [("start",{}),("needs_tools",{}),("tools_done",{}),("done",{})]:
        sm.send(ev, ctx)
    print(json.dumps({"state": sm.state, "history": sm.history}, indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
