"""Short-term conversational memory for multi-turn RAG."""

from __future__ import annotations

from dataclasses import dataclass, field

from ragkit.types import Message, Trust


@dataclass
class ConversationMemory:
    """Ring-buffer of recent user/assistant turns (not long-term vector memory)."""

    max_turns: int = 6
    _messages: list[Message] = field(default_factory=list)

    def __len__(self) -> int:
        # count user turns as "turns"
        return sum(1 for m in self._messages if m.role == "user")

    def add_user(self, content: str) -> None:
        self._messages.append(Message(role="user", content=content, trust=Trust.USER))
        self._trim()

    def add_assistant(self, content: str) -> None:
        self._messages.append(
            Message(role="assistant", content=content, trust=Trust.ASSISTANT)
        )
        self._trim()

    def _trim(self) -> None:
        # keep last max_turns user messages (+ their assistant replies)
        while self.__len__() > self.max_turns:
            # drop from the front
            if self._messages:
                self._messages.pop(0)
            else:
                break
            # if we dropped a user, also drop following assistant if orphaned at start
            while self._messages and self._messages[0].role == "assistant":
                self._messages.pop(0)

    def history(self) -> list[Message]:
        return list(self._messages)

    def render(self) -> str:
        if not self._messages:
            return ""
        lines = []
        for m in self._messages:
            lines.append(f"{m.role.upper()}: {m.content}")
        return "\n".join(lines)

    def clear(self) -> None:
        self._messages.clear()
