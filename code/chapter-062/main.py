#!/usr/bin/env python3
import json
from deploykit import EnvConfig, Rollout, render_env_file
def main():
    cfg=EnvConfig("prod", "ghcr.io/acme/agent:1.2.3", replicas=3, env={"DATABASE_URL":"postgres://..."})
    plan=Rollout("canary", 10).plan("ghcr.io/acme/agent:1.2.2", cfg.image)
    print(json.dumps({"valid": cfg.validate(), "plan": plan, "env": render_env_file(cfg)}, indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
