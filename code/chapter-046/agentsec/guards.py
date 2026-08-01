"""Agent security guards: injection heuristics, sandbox policy, secret redaction."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_INJECTION = re.compile(
    r"(ignore (all )?(previous|prior) instructions|system prompt|jailbreak|exfiltrat)",
    re.I,
)
_SECRET = re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*([\w-]{8,})")


@dataclass
class SecurityReport:
    allowed: bool
    reasons: list[str]
    redacted_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reasons": self.reasons,
            "redacted_text": self.redacted_text,
        }


class SecurityGuard:
    def __init__(self, *, allow_shell: bool = False) -> None:
        self.allow_shell = allow_shell

    def inspect_untrusted_text(self, text: str) -> SecurityReport:
        reasons: list[str] = []
        if _INJECTION.search(text or ""):
            reasons.append("possible_prompt_injection")
        redacted = _SECRET.sub(r"\1=[REDACTED]", text or "")
        if redacted != (text or ""):
            reasons.append("secrets_redacted")
        return SecurityReport(True, reasons, redacted)

    def authorize_tool(
        self,
        tool: str,
        args: dict[str, Any],
        *,
        untrusted_context: str = "",
    ) -> dict[str, Any]:
        report = self.inspect_untrusted_text(untrusted_context)
        if tool in {"run_shell", "bash", "exec"} and not self.allow_shell:
            return {"ok": False, "error": "tool_sandboxed", "report": report.to_dict()}
        if "possible_prompt_injection" in report.reasons and tool.startswith("admin_"):
            return {
                "ok": False,
                "error": "injection_blocks_admin_tool",
                "report": report.to_dict(),
            }
        clean: dict[str, Any] = {}
        for k, v in args.items():
            if isinstance(v, str):
                clean[k] = _SECRET.sub(r"\1=[REDACTED]", v)
            else:
                clean[k] = v
        return {"ok": True, "args": clean, "report": report.to_dict()}
