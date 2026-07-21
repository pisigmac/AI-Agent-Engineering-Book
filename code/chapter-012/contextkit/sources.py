"""Expand ContextState into normalized ContextItem values."""

from __future__ import annotations

from contextkit.types import (
    ContextItem,
    ContextState,
    Kind,
    Priority,
    Trust,
)


def materialize(state: ContextState) -> list[ContextItem]:
    """Flatten snapshot into items with stable ids and recency indexes."""
    items: list[ContextItem] = []
    index = 0

    items.append(
        ContextItem(
            item_id="system:policy",
            kind=Kind.SYSTEM,
            role="system",
            content=state.system_policy.strip(),
            trust=Trust.TRUSTED,
            priority=Priority.CRITICAL,
            created_index=index,
            metadata={"policy_id": state.policy_id},
        )
    )
    index += 1

    if state.goal.strip():
        items.append(
            ContextItem(
                item_id="goal:active",
                kind=Kind.GOAL,
                role="user",
                content=f"Active goal:\n{state.goal.strip()}",
                trust=Trust.UNTRUSTED,
                priority=Priority.HIGH,
                created_index=index,
            )
        )
        index += 1

    for turn_i, turn in enumerate(state.history):
        turn_id = turn.turn_id or f"hist:{turn_i}"
        role = turn.role if turn.role in {"user", "assistant", "system", "tool"} else "user"
        trust = Trust.TRUSTED if role == "system" else Trust.UNTRUSTED
        # Prior assistant text is model-generated; still not policy.
        if role == "assistant":
            trust = Trust.UNTRUSTED
        items.append(
            ContextItem(
                item_id=turn_id,
                kind=Kind.HISTORY,
                role=role,
                content=turn.content,
                trust=trust,
                priority=turn.priority,
                created_index=index,
            )
        )
        index += 1

    for tool in state.tools:
        items.append(
            ContextItem(
                item_id=f"tool:{tool.call_id}",
                kind=Kind.TOOL,
                role="tool",
                content=tool.content,
                trust=Trust.UNTRUSTED,
                priority=tool.priority,
                created_index=index,
                metadata={"tool_name": tool.name, "call_id": tool.call_id},
            )
        )
        index += 1

    for mem in state.memories:
        header = f"source={mem.source or 'unknown'} id={mem.memory_id} score={mem.score:.3f}"
        items.append(
            ContextItem(
                item_id=f"memory:{mem.memory_id}",
                kind=Kind.MEMORY,
                role="user",
                content=f"{header}\n{mem.content}",
                trust=Trust.UNTRUSTED,
                priority=mem.priority,
                created_index=index,
                metadata={
                    "memory_id": mem.memory_id,
                    "score": mem.score,
                    "source": mem.source,
                },
            )
        )
        index += 1

    return items
