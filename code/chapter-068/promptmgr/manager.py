"""Versioned prompt templates with variables."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import re

_VAR = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

@dataclass
class PromptTemplate:
    name: str
    version: str
    body: str
    def render(self, **variables: Any) -> str:
        missing = [v for v in _VAR.findall(self.body) if v not in variables]
        if missing:
            raise KeyError(f"missing variables: {missing}")
        out = self.body
        for k, v in variables.items():
            out = out.replace("{" + k + "}", str(v))
        return out

@dataclass
class PromptManager:
    templates: dict[str, PromptTemplate] = field(default_factory=dict)
    def register(self, tmpl: PromptTemplate) -> None:
        self.templates[f"{tmpl.name}@{tmpl.version}"] = tmpl
        self.templates[tmpl.name] = tmpl
    def get(self, name: str, version: str | None = None) -> PromptTemplate:
        key = f"{name}@{version}" if version else name
        if key not in self.templates:
            raise KeyError(key)
        return self.templates[key]
    def render(self, name: str, version: str | None = None, **variables: Any) -> str:
        return self.get(name, version).render(**variables)

def default_manager() -> PromptManager:
    m = PromptManager()
    m.register(PromptTemplate("support", "1.0.0", "You are support. User: {issue}"))
    m.register(PromptTemplate("support", "1.1.0", "You are support for {product}. User: {issue}"))
    return m
