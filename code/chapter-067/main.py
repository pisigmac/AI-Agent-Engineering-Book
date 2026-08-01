#!/usr/bin/env python3
import json
from llmclient import LLMClient, MockProvider
def main():
    c=LLMClient(MockProvider())
    print(json.dumps({"complete": c.complete([{"role":"user","content":"hello"}]), "stream": c.stream([{"role":"user","content":"stream me"}])}, indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
