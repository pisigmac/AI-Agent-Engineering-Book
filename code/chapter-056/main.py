#!/usr/bin/env python3
import json
from apikit import build_app, Request
def main():
    app = build_app()
    r1 = app.handle(Request("/health"))
    r2 = app.handle(Request("/v1/chat", "POST", headers={"x-api-key":"dev-key"}, json_body={"message":"hi"}))
    r3 = app.handle(Request("/v1/chat", "POST", json_body={"message":"no key"}))
    print(json.dumps({"health": r1.to_dict(), "chat": r2.to_dict(), "unauth": r3.to_dict()}, indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
