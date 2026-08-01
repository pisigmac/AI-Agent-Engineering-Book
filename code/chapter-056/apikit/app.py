"""Minimal FastAPI-like agent API with streaming and auth hooks (stdlib)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator
import json, hashlib, time

Handler = Callable[[dict[str, Any]], dict[str, Any] | Iterator[str]]

@dataclass
class Request:
    path: str
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    json_body: dict[str, Any] = field(default_factory=dict)
    query: dict[str, str] = field(default_factory=dict)

@dataclass
class Response:
    status: int
    body: Any
    headers: dict[str, str] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "body": self.body, "headers": self.headers}

class App:
    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], Handler] = {}
        self.api_keys: dict[str, str] = {"dev-key": "user"}
    def add_api_route(self, path: str, methods: list[str], handler: Handler) -> None:
        for m in methods:
            self.routes[(m.upper(), path)] = handler
    def get(self, path: str):
        def deco(fn): self.add_api_route(path, ["GET"], fn); return fn
        return deco
    def post(self, path: str):
        def deco(fn): self.add_api_route(path, ["POST"], fn); return fn
        return deco
    def auth(self, req: Request) -> str | None:
        key = req.headers.get("x-api-key") or req.headers.get("authorization", "").removeprefix("Bearer ").strip()
        return self.api_keys.get(key)
    def handle(self, req: Request) -> Response:
        user = self.auth(req)
        if req.path not in {"/health"} and user is None and req.method != "GET" or (req.path.startswith("/v1/") and user is None):
            if req.path.startswith("/v1/"):
                return Response(401, {"error": "unauthorized"})
        handler = self.routes.get((req.method, req.path))
        if not handler:
            return Response(404, {"error": "not_found"})
        try:
            out = handler({"request": req, "user": user})
            if hasattr(out, "__iter__") and not isinstance(out, (dict, list, str)):
                # streaming
                chunks = list(out)
                return Response(200, {"stream": chunks}, headers={"content-type": "text/event-stream"})
            return Response(200, out)
        except Exception as e:  # noqa: BLE001
            return Response(500, {"error": str(e)})

def build_app() -> App:
    app = App()
    @app.get("/health")
    def health(_):
        return {"status": "ok", "ts": time.time()}
    @app.post("/v1/chat")
    def chat(ctx):
        req: Request = ctx["request"]
        msg = req.json_body.get("message", "")
        return {"id": hashlib.sha1(msg.encode()).hexdigest()[:10], "reply": f"echo:{msg}", "user": ctx["user"]}
    @app.post("/v1/chat/stream")
    def stream(ctx):
        msg = ctx["request"].json_body.get("message", "")
        def gen():
            for part in (f"data: thinking about {msg}\n\n", "data: done\n\n"):
                yield part
        return gen()
    return app
