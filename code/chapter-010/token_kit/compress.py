"""Compression helpers: tool caps, sliding window, summary placeholders."""

from __future__ import annotations

from token_kit.tokenizers import TokenCounter
from token_kit.types import ChatMessage, Priority, Role


TRUNCATION_MARKER = "\n\n[truncated: content exceeded token/char cap]"


def cap_text(text: str, counter: TokenCounter, *, max_tokens: int) -> tuple[str, bool]:
    if max_tokens <= 0:
        return TRUNCATION_MARKER.strip(), True
    if counter.count_text(text) <= max_tokens:
        return text, False
    # Binary search character cut as a practical approximation
    lo, hi = 0, len(text)
    best = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        candidate = text[:mid] + TRUNCATION_MARKER
        if counter.count_text(candidate) <= max_tokens:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return text[:best] + TRUNCATION_MARKER, True


def cap_tool_messages(
    messages: list[ChatMessage],
    counter: TokenCounter,
    *,
    max_tokens_per_tool: int = 1024,
) -> list[ChatMessage]:
    out: list[ChatMessage] = []
    for msg in messages:
        if msg.role is not Role.TOOL:
            out.append(msg)
            continue
        content, truncated = cap_text(msg.content, counter, max_tokens=max_tokens_per_tool)
        meta = dict(msg.metadata)
        if truncated:
            meta["truncated"] = True
            meta["original_chars"] = len(msg.content)
        out.append(
            ChatMessage(
                role=msg.role,
                content=content,
                name=msg.name,
                message_id=msg.message_id,
                priority=msg.priority or Priority.NORMAL,
                metadata=meta,
            )
        )
    return out


def sliding_window(messages: list[ChatMessage], *, keep_last: int) -> list[ChatMessage]:
    """Keep all system messages + last N non-system messages."""
    if keep_last < 0:
        raise ValueError("keep_last must be >= 0")
    systems = [m for m in messages if m.role is Role.SYSTEM]
    rest = [m for m in messages if m.role is not Role.SYSTEM]
    if keep_last == 0:
        return systems
    return systems + rest[-keep_last:]


def inject_summary_message(
    summary: str,
    *,
    message_id: str = "summary-slot",
) -> ChatMessage:
    return ChatMessage(
        role=Role.SYSTEM,
        content=f"Conversation summary (lossy compression):\n{summary}",
        message_id=message_id,
        priority=Priority.HIGH,
        metadata={"kind": "summary"},
    )
