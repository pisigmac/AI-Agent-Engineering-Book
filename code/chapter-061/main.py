#!/usr/bin/env python3
import json
from authkit import AuthService
def main():
    a=AuthService(); key=a.issue_api_key("u1", {"support"}); tok=a.issue_token("u2", {"viewer"})
    p=a.authenticate(key)
    print(json.dumps({"key_auth": p.subject if p else None, "can_chat": a.authorize(p, "chat"), "viewer_chat": a.authorize(a.authenticate(tok), "chat")}, indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
