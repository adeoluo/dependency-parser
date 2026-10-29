"""A deterministic micro-benchmark for training and parsing throughput.

Measures parser training time and greedy decoding throughput on the bundled
treebank, plus the held-out attachment scores and a naive baseline for context.
Deterministic and offline; run with:

    uv run python benchmarks/benchmark.py
"""

from __future__ import annotations

import time

from dependency_parser.data import Sentence, test_data, train_data
from dependency_parser.evaluation import AttachmentReport, evaluate
from dependency_parser.parser import Parser, TrainingConfig


def _left_branching_baseline(sentences: list[Sentence]) -> float:
    """Score of attaching every token to the immediately preceding token."""

    tokens = 0
    correct = 0
    for sentence in sentences:
        for index, token in enumerate(sentence, start=1):
            tokens += 1
            if token.head == index - 1:
                correct += 1
    return correct / tokens if tokens else 0.0


def main() -> None:
    data = train_data()
    start = time.perf_counter()
    parser = Parser.train(data, TrainingConfig(epochs=10, seed=0))
    train_ms = (time.perf_counter() - start) * 1000

    held_out = test_data()
    report: AttachmentReport = evaluate(parser, held_out)

    sentences = held_out * 20
    start = time.perf_counter()
    for sentence in sentences:
        parser.parse(sentence)
    decode_s = time.perf_counter() - start

    print(f"Train sentences: {len(data)} | Held-out sentences: {len(held_out)}")
    print(f"Training (10 epochs): {train_ms:.0f} ms")
    print(f"Held-out UAS: {report.uas:.4f}  LAS: {report.las:.4f}")
    print(f"Left-branching baseline UAS: {_left_branching_baseline(held_out):.4f}")
    print(f"Greedy decoding: {len(sentences) / decode_s:.0f} sentences/sec")


if __name__ == "__main__":
    main()
