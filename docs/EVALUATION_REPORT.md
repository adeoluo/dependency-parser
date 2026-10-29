# Evaluation Report - Dependency Parser

> Reproduce with `python -m dependency_parser evaluate` (scores) and
> `uv run python benchmarks/benchmark.py` (scores plus throughput). Evaluation is
> deterministic: training and decoding are fully seeded, so every number here is exact rather
> than an average over seeds.

## Setup
- **Training data:** 400 projective trees generated from seed 1.
- **Held-out data:** 100 projective trees generated from the disjoint seed 9999 (663 scored
  tokens, excluding the artificial root).
- **Model:** averaged structured perceptron over arc-standard transitions, 10 training epochs.
- **Decoding:** greedy argmax over legal transitions.

## Metrics
- **UAS (unlabeled attachment score):** fraction of tokens attached to the correct head.
- **LAS (labeled attachment score):** fraction of tokens with the correct head and relation.

## Results

| Metric | Value |
|---|---:|
| UAS | 0.9879 |
| LAS | 0.9879 |
| left-branching baseline UAS | 0.0558 |
| scored tokens | 663 |

Training completes in roughly one and a half seconds and the parser decodes several thousand
sentences per second on a single core.

## Error analysis
The residual errors are overwhelmingly **prepositional attachments**. The treebank makes some
prepositions lean toward noun attachment and others toward verb attachment, with a deliberate
irreducible residue that no feature of the observable tokens can resolve. The parser learns the
per-preposition bias, so its errors sit at the floor set by that ambiguity rather than being
spread across easy constructions. UAS and LAS coincide because, once a head is correct, the
grammar determines its relation unambiguously.

## Baseline
The left-branching baseline attaches every token to the immediately preceding word. It reaches
only 0.0558 UAS because most dependents in this grammar precede their heads (determiners and
adjectives attach to the following noun, subjects to the following verb), which the trained
parser captures and the baseline cannot.
