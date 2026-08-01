#!/usr/bin/env python3
import json
from fwsched import Scheduler
def main():
    s=Scheduler(); out=[]; s.schedule("a", lambda: out.append("a"), priority=1, delay_s=0); s.schedule("b", lambda: out.append("b"), priority=2, interval_s=2)
    print(json.dumps({"t1": s.tick(0), "t2": s.tick(2), "hist": s.history}, indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
