"""Execute validated tool calls with timeout and structured errors."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from typing import Any

from toolcall.registry import ToolRegistry
from toolcall.specs import ToolObservation
from toolcall.validate_call import ToolCallValidationError, validate_tool_arguments


class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> ToolObservation:
        started = time.perf_counter()
        arguments = arguments or {}
        try:
            args_obj = validate_tool_arguments(self.registry, name, arguments)
        except ToolCallValidationError as exc:
            return ToolObservation(
                ok=False,
                name=name,
                error_code=exc.code,
                error_message=str(exc),
                latency_s=time.perf_counter() - started,
            )

        spec = self.registry.get(name)
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(self._invoke, spec.handler, args_obj)
                result = fut.result(timeout=spec.timeout_s)
            return ToolObservation(
                ok=True,
                name=name,
                result=result,
                latency_s=time.perf_counter() - started,
            )
        except FuturesTimeout:
            return ToolObservation(
                ok=False,
                name=name,
                error_code="timeout",
                error_message=f"tool exceeded {spec.timeout_s}s",
                latency_s=time.perf_counter() - started,
            )
        except Exception as exc:  # noqa: BLE001 — boundary
            return ToolObservation(
                ok=False,
                name=name,
                error_code="execution_error",
                error_message=str(exc),
                latency_s=time.perf_counter() - started,
            )

    @staticmethod
    def _invoke(handler: Any, args_obj: Any) -> Any:
        # Prefer model_dump for pydantic v2 objects
        if hasattr(args_obj, "model_dump"):
            data = args_obj.model_dump()
            return handler(**data)
        return handler(args_obj)
