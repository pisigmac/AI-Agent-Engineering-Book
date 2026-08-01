#!/usr/bin/env python3
from logkit import Logger
def main():
    log=Logger("agent-api"); log.info("request", path="/v1/chat"); log.bind(user="u1").error("failed", code=500)
    print(log.dump()); return 0
if __name__=="__main__": raise SystemExit(main())
