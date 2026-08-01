#!/usr/bin/env python3
import json
from promptmgr import default_manager
def main():
    m=default_manager()
    print(json.dumps({"v11": m.render("support", product="Acme", issue="refund"), "v10": m.render("support", version="1.0.0", issue="late ship")}, indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
