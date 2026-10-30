"""A deterministic scale benchmark for greedy dependency-parsing throughput.

Trains the transition-based parser once, then runs greedy decoding over
progressively larger synthetic treebanks produced by ``data.generate_corpus``.
Because the generator composes projective trees from a known grammar, every gold
head is correct by construction, so unlabeled attachment score (UAS) is an exact
quality metric. For each workload the benchmark reports wall-clock seconds,
parsing throughput in sentences per second, peak memory in MiB measured with the
standard-library ``tracemalloc`` module, and UAS.

Timing is measured without tracemalloc (which otherwise slows every allocation);
peak memory is traced separately around the treebank plus a single parse, which
is faithful because sentences are parsed one at a time. The treebank is
synthetic. This pure-Python from-scratch implementation is not competitive on
wall-clock time with compiled parsers; the goal is to show how greedy decoding
scales with the number of sentences. Deterministic and offline; run with:

    uv run python benchmarks/scale.py
"""

from __future__ import annotations

import time
import tracemalloc
from dataclasses import dataclass

from dependency_parser.data import generate_corpus, train_data
from dependency_parser.evaluation import evaluate
from dependency_parser.parser import Parser, TrainingConfig

WORKLOAD_SIZES: tuple[int, ...] = (1000, 2000, 4000, 8000)
CORPUS_SEED = 123
_BYTES_PER_MIB = 1024 * 1024


@dataclass(frozen=True)
class ScaleRow:
    """One measured workload: size, timing, throughput, memory, and quality."""

    size: int
    seconds: float
    throughput: float
    peak_mib: float
    uas: float


def _train() -> Parser:
    return Parser.train(train_data(), TrainingConfig(epochs=10, seed=0))


def _peak_mib(parser: Parser, size: int) -> float:
    """Peak memory to hold a treebank of ``size`` sentences and run one parse."""

    tracemalloc.start()
    tracemalloc.reset_peak()
    corpus = generate_corpus(size, seed=CORPUS_SEED)
    parser.parse(corpus[0])
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / _BYTES_PER_MIB


def run_scale(sizes: tuple[int, ...] = WORKLOAD_SIZES) -> list[ScaleRow]:
    """Train once, then measure greedy-decoding scaling across treebank sizes."""

    parser = _train()
    rows: list[ScaleRow] = []
    for size in sizes:
        corpus = generate_corpus(size, seed=CORPUS_SEED)
        start = time.perf_counter()
        report = evaluate(parser, corpus)
        elapsed = time.perf_counter() - start
        rows.append(
            ScaleRow(
                size=size,
                seconds=elapsed,
                throughput=size / elapsed if elapsed else 0.0,
                peak_mib=_peak_mib(parser, size),
                uas=report.uas,
            )
        )
    return rows


def main() -> None:
    print("Synthetic grammar-generated treebank; from-scratch transition-based parser.")
    print("Pure-Python greedy decoding; not benchmarked against compiled parsers.")
    print(f"{'sentences':>10}  {'seconds':>9}  {'sent/sec':>9}  {'peak MiB':>9}  {'UAS':>7}")
    for row in run_scale():
        print(
            f"{row.size:>10d}  {row.seconds:>9.3f}  {row.throughput:>9.1f}  "
            f"{row.peak_mib:>9.2f}  {row.uas:>7.3f}"
        )


if __name__ == "__main__":
    main()
