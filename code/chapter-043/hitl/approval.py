"""Human-in-the-loop: approval gates, interrupts, escalation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ApprovalRequest:
    id: str
    action: str
    risk: str
    payload: dict[str, Any]
    status: str = "pending"  # pending|approved|rejected|escalated

@dataclass
class HITLController:
    pending: dict[str, ApprovalRequest] = field(default_factory=dict)
    log: list[dict[str, Any]] = field(default_factory=list)
    _seq: int = 0

    def request(self, action: str, payload: dict[str, Any], *, risk: str = "medium") -> ApprovalRequest:
        self._seq += 1
        req = ApprovalRequest(id=f"apr-{self._seq}", action=action, risk=risk, payload=payload)
        if risk == "low":
            req.status = "approved"
            self.log.append({"id": req.id, "auto": True, "status": "approved"})
        else:
            self.pending[req.id] = req
            self.log.append({"id": req.id, "status": "pending", "risk": risk})
        return req

    def approve(self, req_id: str) -> ApprovalRequest:
        req = self.pending.pop(req_id)
        req.status = "approved"
        self.log.append({"id": req_id, "status": "approved"})
        return req

    def reject(self, req_id: str) -> ApprovalRequest:
        req = self.pending.pop(req_id)
        req.status = "rejected"
        self.log.append({"id": req_id, "status": "rejected"})
        return req

    def escalate(self, req_id: str) -> ApprovalRequest:
        req = self.pending[req_id]
        req.status = "escalated"
        self.log.append({"id": req_id, "status": "escalated"})
        return req

    def run_action(self, action: str, payload: dict[str, Any], *, risk: str = "medium", auto_approve: bool = False) -> dict[str, Any]:
        req = self.request(action, payload, risk=risk)
        if req.status == "pending" and auto_approve:
            req = self.approve(req.id)
        if req.status != "approved":
            return {"ok": False, "status": req.status, "request_id": req.id, "interrupted": True}
        return {"ok": True, "status": "executed", "action": action, "payload": payload, "request_id": req.id}
