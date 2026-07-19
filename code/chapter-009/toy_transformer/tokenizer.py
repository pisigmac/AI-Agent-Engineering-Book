"""Tiny whitespace tokenizer with a fixed teaching vocabulary."""

from __future__ import annotations

from dataclasses import dataclass


SPECIAL = ["<pad>", "<bos>", "<eos>", "<unk>"]


DEFAULT_VOCAB = SPECIAL + [
    "hello",
    "agent",
    "world",
    "tool",
    "model",
    "token",
    "attention",
    "layer",
    "decode",
    "context",
    "python",
    "async",
    "http",
    "error",
    "the",
    "a",
    "to",
    "is",
    "and",
    "of",
]


@dataclass
class TinyTokenizer:
    vocab: list[str]

    def __post_init__(self) -> None:
        self.token_to_id = {t: i for i, t in enumerate(self.vocab)}
        self.id_to_token = list(self.vocab)
        for i, name in enumerate(SPECIAL):
            if name not in self.token_to_id:
                raise ValueError(f"missing special token {name}")
        self.pad_id = self.token_to_id["<pad>"]
        self.bos_id = self.token_to_id["<bos>"]
        self.eos_id = self.token_to_id["<eos>"]
        self.unk_id = self.token_to_id["<unk>"]

    @classmethod
    def default(cls) -> "TinyTokenizer":
        return cls(list(DEFAULT_VOCAB))

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    def encode(self, text: str, *, add_bos: bool = True, add_eos: bool = False) -> list[int]:
        parts = [p.lower() for p in text.strip().split() if p]
        ids: list[int] = []
        if add_bos:
            ids.append(self.bos_id)
        for p in parts:
            ids.append(self.token_to_id.get(p, self.unk_id))
        if add_eos:
            ids.append(self.eos_id)
        return ids

    def decode(self, ids: list[int], *, skip_special: bool = True) -> str:
        toks: list[str] = []
        for i in ids:
            tok = self.id_to_token[i] if 0 <= i < len(self.id_to_token) else "<unk>"
            if skip_special and tok in SPECIAL:
                continue
            toks.append(tok)
        return " ".join(toks)
