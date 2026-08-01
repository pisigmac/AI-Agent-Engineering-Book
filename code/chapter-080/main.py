#!/usr/bin/env python3
import json
from fwplugins import Plugin, PluginManager
def main():
    pm=PluginManager(); pm.allow("greeter"); pm.register(Plugin("greeter","on_message", lambda m: f"hi {m}"), trusted=False)
    print(json.dumps(pm.invoke("on_message", "ada"), indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
