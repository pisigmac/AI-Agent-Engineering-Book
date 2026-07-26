"""Streaming completion usage aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator


@dataclass
class StreamChunk:
    text: str
    output_tokens_delta: int = 0
    done: bool = False


@dataclass
class StreamAccumulator:
    """Aggregate streamed tokens into final usage for billing."""

    model_id: str
    input_tokens: int
    output_tokens: int = 0
    text_parts: list[str] = field(default_factory=list)
    chunks: int = 0

    def push(self, chunk: StreamChunk) -> None:
        self.chunks += 1
        if chunk.text:
            self.text_parts.append(chunk.text)
        if chunk.output_tokens_delta:
            self.output_tokens += chunk.output_tokens_delta
        elif chunk.text:
            # heuristic when provider omits per-chunk token counts
            self.output_tokens += max(1, len(chunk.text) // 4)

    @property
    def text(self) -> str:
        return "".join(self.text_parts)

    def finalize(self) -> tuple[str, int, int]:
        return self.text, self.input_tokens, self.output_tokens


def iter_mock_stream(text: str, *, chunk_chars: int = 12) -> Iterator[StreamChunk]:
    if chunk_chars < 1:
        raise ValueError("chunk_chars must be >= 1")
    if not text:
        yield StreamChunk("", 0, done=True)
        return
    for i in range(0, len(text), chunk_chars):
        part = text[i : i + chunk_chars]
        last = i + chunk_chars >= len(text)
        yield StreamChunk(part, max(1, len(part) // 4), done=last)


def consume_stream(chunks: Iterable[StreamChunk], *, model_id: str, input_tokens: int) -> StreamAccumulator:
    acc = StreamAccumulator(model_id=model_id, input_tokens=input_tokens)
    for ch in chunks:
        acc.push(ch)
    return acc
