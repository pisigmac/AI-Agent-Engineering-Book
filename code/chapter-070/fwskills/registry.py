"""Framework skill registry: discovery and composition."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class Skill:
    name: str
    description: str
    handler: Callable[[str], str]
    tags: tuple[str, ...] = ()

class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill
    def get(self, name: str) -> Skill:
        return self._skills[name]
    def discover(self, tag: str) -> list[str]:
        return [s.name for s in self._skills.values() if tag in s.tags]
    def compose(self, names: list[str], text: str) -> str:
        cur = text
        for n in names:
            cur = self.get(n).handler(cur)
        return cur

def default_registry() -> SkillRegistry:
    r = SkillRegistry()
    r.register(Skill("lower", "lowercase", lambda t: t.lower(), ("text",)))
    r.register(Skill("exclaim", "add bang", lambda t: t + "!", ("text",)))
    return r
