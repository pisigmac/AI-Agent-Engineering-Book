"""Deployment config and rollout strategies."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class EnvConfig:
    name: str
    image: str
    replicas: int = 1
    env: dict[str, str] = field(default_factory=dict)
    def validate(self) -> list[str]:
        errs = []
        if not self.image:
            errs.append("missing_image")
        if self.replicas < 1:
            errs.append("replicas")
        if "DATABASE_URL" not in self.env:
            errs.append("missing_DATABASE_URL")
        return errs

@dataclass
class Rollout:
    strategy: str = "rolling"
    percent: int = 100
    def plan(self, current: str, target: str) -> list[dict[str, Any]]:
        if self.strategy == "blue_green":
            return [
                {"action": "deploy_green", "image": target},
                {"action": "smoke_test", "target": "green"},
                {"action": "switch_traffic", "to": "green"},
                {"action": "retire_blue", "image": current},
            ]
        if self.strategy == "canary":
            return [
                {"action": "deploy_canary", "image": target, "percent": min(self.percent, 20)},
                {"action": "observe", "minutes": 15},
                {"action": "promote", "percent": 100},
            ]
        return [
            {"action": "rolling_update", "from": current, "to": target},
            {"action": "healthcheck"},
        ]

def render_env_file(cfg: EnvConfig) -> str:
    lines = [f"APP_ENV={cfg.name}", f"IMAGE={cfg.image}"]
    for k, v in cfg.env.items():
        lines.append(f"{k}={v}")
    return chr(10).join(lines) + chr(10)
