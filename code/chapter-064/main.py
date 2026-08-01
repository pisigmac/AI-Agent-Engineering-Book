#!/usr/bin/env python3
import json
from monkit import SLO, Monitor
def main():
    s=SLO("api-availability", 0.99)
    for ok in [True]*98 + [False]*3:
        s.record(ok=ok)
    m=Monitor([s]); print(json.dumps(m.dashboard(), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
