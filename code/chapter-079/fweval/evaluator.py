"""Framework evaluator: scorers, datasets, release gates."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

Scorer = Callable[[str, str], float]  # pred, gold -> 0..1

@dataclass
class Example:
    id: str
    input: str
    gold: str

@dataclass
class Evaluator:
    scorer: Scorer
    gate: float = 0.8
    def evaluate(self, predict: Callable[[str], str], dataset: list[Example]) -> dict[str, Any]:
        rows = []
        total = 0.0
        for ex in dataset:
            pred = predict(ex.input)
            score = self.scorer(pred, ex.gold)
            total += score
            rows.append({"id": ex.id, "score": score, "pred": pred, "gold": ex.gold})
        avg = total / max(len(dataset), 1)
        return {"n": len(dataset), "avg_score": round(avg, 4), "pass": avg >= self.gate, "rows": rows}

def exact_scorer(pred: str, gold: str) -> float:
    return 1.0 if pred.strip().lower() == gold.strip().lower() else 0.0
