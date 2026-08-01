"""Framework tool registry with schema + permissions."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[..., Any]
    schema: dict[str, type] = field(default_factory=dict)
    permissions: tuple[str, ...] = ("default",)

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool
    def list(self) -> list[dict[str, Any]]:
        return [{"name": t.name, "description": t.description, "permissions": list(t.permissions)} for t in self._tools.values()]
    def call(self, name: str, args: dict[str, Any], *, roles: tuple[str, ...] = ("default",)) -> dict[str, Any]:
        if name not in self._tools:
            return {"ok": False, "error": "unknown_tool"}
        t = self._tools[name]
        if not (set(t.permissions) & set(roles) or "admin" in roles):
            return {"ok": False, "error": "forbidden"}
        for k, typ in t.schema.items():
            if k not in args or not isinstance(args[k], typ):
                return {"ok": False, "error": f"invalid_arg:{k}"}
        try:
            return {"ok": True, "result": t.handler(**args)}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e)}

def default_registry() -> ToolRegistry:
    r = ToolRegistry()
    r.register(Tool("echo", "echo text", lambda text: text, {"text": str}))
    r.register(Tool("add", "add ints", lambda a, b: a + b, {"a": int, "b": int}, ("default", "math")))
    return r
