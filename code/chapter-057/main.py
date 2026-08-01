#!/usr/bin/env python3
import json
from workers import JobQueue
def main():
    n={"i":0}
    def handler(p):
        if p.get("fail_once") and n["i"]==0:
            n["i"]+=1; raise RuntimeError("transient")
        return {"echo": p}
    q=JobQueue(handler)
    q.enqueue({"x":1}); q.enqueue({"fail_once": True})
    print(json.dumps(q.drain(), indent=2)); print(json.dumps({"done": q.done, "dead": q.dead_letter}, indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
