"""In-process event bus for event-driven agents (queue + pubsub)."""
from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable

Handler = Callable[[dict[str, Any]], None]

@dataclass
class EventBus:
    queues: dict[str, deque] = field(default_factory=lambda: defaultdict(deque))
    subscribers: dict[str, list[Handler]] = field(default_factory=lambda: defaultdict(list))
    dead_letter: list[dict[str, Any]] = field(default_factory=list)

    def publish(self, topic: str, event: dict[str, Any]) -> None:
        payload = {"topic": topic, **event}
        self.queues[topic].append(payload)
        for h in list(self.subscribers[topic]):
            try:
                h(payload)
            except Exception as e:  # noqa: BLE001
                self.dead_letter.append({"topic": topic, "error": str(e), "event": payload})

    def subscribe(self, topic: str, handler: Handler) -> None:
        self.subscribers[topic].append(handler)

    def consume(self, topic: str, n: int = 1) -> list[dict[str, Any]]:
        out = []
        q = self.queues[topic]
        for _ in range(min(n, len(q))):
            out.append(q.popleft())
        return out

def demo_ticket_flow() -> dict[str, Any]:
    bus = EventBus()
    handled: list[str] = []
    bus.subscribe("ticket.created", lambda e: handled.append(f"triage:{e.get('id')}"))
    bus.subscribe("ticket.created", lambda e: bus.publish("ticket.enriched", {"id": e.get("id"), "priority": "normal"}))
    bus.subscribe("ticket.enriched", lambda e: handled.append(f"route:{e.get('id')}:{e.get('priority')}"))
    bus.publish("ticket.created", {"id": "T-1", "text": "refund"})
    return {"handled": handled, "queued_enriched": len(bus.queues["ticket.enriched"]), "dead_letter": bus.dead_letter}
