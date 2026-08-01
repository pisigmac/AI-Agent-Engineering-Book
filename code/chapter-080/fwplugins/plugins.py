"""Safe plugin registry with extension points (no arbitrary code exec)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

PluginFn = Callable[..., Any]

@dataclass
class Plugin:
    name: str
    extension_point: str
    handler: PluginFn
    version: str = "1.0.0"

@dataclass
class PluginManager:
    plugins: dict[str, list[Plugin]] = field(default_factory=dict)
    allowlist: set[str] = field(default_factory=set)
    def register(self, plugin: Plugin, *, trusted: bool = False) -> None:
        if not trusted and plugin.name not in self.allowlist:
            raise PermissionError(f"plugin not allowlisted: {plugin.name}")
        self.plugins.setdefault(plugin.extension_point, []).append(plugin)
    def allow(self, name: str) -> None:
        self.allowlist.add(name)
    def invoke(self, extension_point: str, *args: Any, **kwargs: Any) -> list[Any]:
        out = []
        for p in self.plugins.get(extension_point, []):
            out.append({"plugin": p.name, "result": p.handler(*args, **kwargs)})
        return out
