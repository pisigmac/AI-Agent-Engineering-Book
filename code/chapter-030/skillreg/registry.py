"""Skill registry with discovery and composition."""
from __future__ import annotations
from typing import Any
from skillreg.skill import Skill, SkillSpec

class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
    def register(self, skill: Skill) -> None:
        key = f"{skill.spec.name}@{skill.spec.version}"
        self._skills[key] = skill
        self._skills[skill.spec.name] = skill  # latest alias
    def get(self, name: str, version: str | None = None) -> Skill:
        key = f"{name}@{version}" if version else name
        if key not in self._skills:
            raise KeyError(f"unknown skill: {key}")
        return self._skills[key]
    def list(self) -> list[dict[str, Any]]:
        seen=set(); out=[]
        for s in self._skills.values():
            k=f"{s.spec.name}@{s.spec.version}"
            if k in seen: continue
            seen.add(k)
            out.append({"name": s.spec.name, "version": s.spec.version, "description": s.spec.description, "tags": list(s.spec.tags)})
        return out
    def discover(self, tag: str) -> list[str]:
        return [s.spec.name for s in {id(v):v for v in self._skills.values()}.values() if tag in s.spec.tags]
    def compose(self, names: list[str], text: str) -> str:
        cur = text
        for n in names:
            cur = str(self.get(n).run(text=cur))
        return cur

def default_registry() -> SkillRegistry:
    reg = SkillRegistry()
    reg.register(Skill(SkillSpec("normalize", "lowercase strip", tags=("text",)), lambda text="": text.strip().lower()))
    reg.register(Skill(SkillSpec("summarize", "fake summary", tags=("text","nlp")), lambda text="": f"SUMMARY({len(text)} chars): {text[:80]}"))
    reg.register(Skill(SkillSpec("cite", "wrap citation", tags=("text",), version="1.1.0"), lambda text="": f"{text} [src:kb]"))
    return reg
