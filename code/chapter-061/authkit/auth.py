"""API keys, simple bearer tokens, and RBAC."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import hashlib, secrets, time

@dataclass
class Principal:
    subject: str
    roles: set[str] = field(default_factory=set)

class AuthService:
    def __init__(self) -> None:
        self.api_keys: dict[str, Principal] = {}
        self.tokens: dict[str, tuple[Principal, float]] = {}
        self.role_perms: dict[str, set[str]] = {
            "admin": {"*"},
            "support": {"chat", "read_kb", "refund_read"},
            "viewer": {"read_kb"},
        }
    def issue_api_key(self, subject: str, roles: set[str]) -> str:
        key = "ak_" + secrets.token_hex(8)
        self.api_keys[key] = Principal(subject, roles)
        return key
    def issue_token(self, subject: str, roles: set[str], *, ttl_s: float = 3600) -> str:
        tok = "tok_" + secrets.token_hex(12)
        self.tokens[tok] = (Principal(subject, roles), time.time() + ttl_s)
        return tok
    def authenticate(self, credential: str) -> Principal | None:
        if credential in self.api_keys:
            return self.api_keys[credential]
        item = self.tokens.get(credential)
        if not item: return None
        principal, exp = item
        if time.time() > exp:
            self.tokens.pop(credential, None); return None
        return principal
    def authorize(self, principal: Principal | None, permission: str) -> bool:
        if principal is None: return False
        for role in principal.roles:
            perms = self.role_perms.get(role, set())
            if "*" in perms or permission in perms:
                return True
        return False
