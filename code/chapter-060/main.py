#!/usr/bin/env python3
import json
from rediskit import RedisLite
def main():
    r=RedisLite(); r.set("k","v", ex=60); r.session_set("s1", {"user":"a"})
    print(json.dumps({"get": r.get("k"), "rl": r.allow_rate("u1", limit=2, window_s=60), "sess": r.session_get("s1")}, indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
