<h1 align="center">Dependency Parser</h1>

<p align="center">
  <em>An arc-standard, transition-based dependency parser built from scratch: a static oracle, an averaged structured perceptron policy, greedy decoding, and attachment-score evaluation.</em>
</p>

<p align="center">
  <a href="https://github.com/adeoluo/dependency-parser/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/adeoluo/dependency-parser/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://github.com/adeoluo/dependency-parser/releases"><img alt="Release" src="https://img.shields.io/github/v/release/adeoluo/dependency-parser"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%20%7C%203.12-blue">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green"></a>
</p>

---

## Motivation

A dependency parse states, for every word in a sentence, which other word it depends on and
how. It is the backbone of relation extraction, question answering, and grammatical analysis.
Transition-based parsing casts this structured prediction problem as a sequence of local
decisions over a stack and a buffer, so a sentence of length *n* is parsed in a linear number
of steps.

This project implements the **arc-standard** system (Nivre, 2004) **from scratch**: the
configuration and transitions, the **static oracle** that turns a gold tree into the transition
sequence that builds it, an **averaged structured perceptron** policy over sparse features, and
greedy decoding, all with no automatic differentiation.

## Architecture

<p align="center">
  <img src="docs/architecture/architecture.svg" alt="Architecture diagram" width="860">
</p>

<sub>Legend: amber = entry points and external systems, indigo = core logic, green = data and state, blue = validation and control, grey = observability and outputs.</sub>

The CLI and the HTTP service both train the parser on the seeded training treebank before use:
the static oracle turns each gold tree into a transition sequence and the averaged perceptron
learns from it with teacher forcing. At parse time a configuration holds a stack, a buffer, and
the arcs committed so far. At each step the perceptron scores every legal transition from the
surrounding words and parts of speech and the highest-scoring one is applied, until the
terminal configuration yields a head and relation per token. Held-out trees are scored with
UAS and LAS, and every route records latency and errors for `/metrics`. See the
[ADRs](docs/adr/) for the key decisions.

### The transition system

The arc-standard system uses three transition families:

- **SHIFT** moves the front of the buffer onto the stack.
- **LEFT(label)** attaches the second stack item as a `label` dependent of the top item, then
  removes the second item.
- **RIGHT(label)** attaches the top stack item as a `label` dependent of the second item, then
  removes the top item.

A **static oracle** maps a gold tree to the unique transition sequence that constructs it,
preferring LEFT, then RIGHT, then SHIFT, and only committing a RIGHT attachment once the top
item has collected all of its own dependents. The policy is an **averaged structured
perceptron**: training follows the oracle sequence with teacher forcing, and on every decision
where the highest-scoring legal transition disagrees with the oracle the weights are moved
toward the oracle transition and away from the prediction. Collins-style averaging is applied
lazily with update timestamps.

### Components

- **data**: a projective treebank generated from a small dependency grammar, with disjoint
  splits and deliberate prepositional-attachment ambiguity.
- **transitions**: the arc-standard configuration, transitions, and the static oracle.
- **features**: sparse feature templates over the stack and buffer context.
- **perceptron**: the averaged structured perceptron with lazy weight averaging.
- **parser**: the training loop and greedy decoder.
- **evaluation**: unlabeled and labeled attachment scoring.

## Results

> Reproduce with `python -m dependency_parser evaluate`. Scoring excludes the artificial root.
> UAS is the fraction of tokens attached to the correct head; LAS additionally requires the
> correct relation label.

| Metric | Value |
|---|---:|
| **unlabeled attachment score (UAS)** | **0.9879** |
| **labeled attachment score (LAS)** | **0.9879** |
| left-branching baseline UAS | 0.0558 |
| held-out tokens | 663 |

On a held-out treebank the from-scratch parser reaches **0.9879 UAS**. The residual errors are
concentrated on genuinely ambiguous **prepositional attachments**: the treebank deliberately
makes some prepositions lean toward noun attachment and others toward verb attachment while
leaving a residue that cannot be resolved from the observable tokens. The parser learns the
per-preposition bias and accepts the irreducible remainder, as a real parser must.

### Scale

`benchmarks/scale.py` trains the parser once, then runs greedy decoding over progressively
larger synthetic treebanks and records wall-clock time, parsing throughput, peak memory
(`tracemalloc`), and UAS. Timing is measured without tracemalloc (which slows every allocation);
peak memory is traced separately around the treebank plus a single parse, which is faithful
because sentences are parsed one at a time. Throughput is roughly flat near 440 to 640 sentences
per second, peak memory grows linearly with the treebank, and UAS stays stable because the same
trained parser is applied at every size. Run with `uv run python benchmarks/scale.py`.

| Sentences | Seconds | Throughput (sent/sec) | Peak memory (MiB) | UAS |
|---:|---:|---:|---:|---:|
| 1000 | 1.57 | 636.0 | 0.86 | 0.980 |
| 2000 | 3.65 | 548.7 | 1.72 | 0.979 |
| 4000 | 7.49 | 534.1 | 3.43 | 0.978 |
| 8000 | 18.21 | 439.3 | 6.88 | 0.979 |

Caveat: the treebank is synthetic and grammar-generated, and this Python implementation is not
benchmarked against compiled parsers.

## Quickstart

```bash
git clone https://github.com/adeoluo/dependency-parser.git && cd dependency-parser
make setup                    # install dev tooling + pre-commit hooks
make all                      # lint + type-check + test

python -m dependency_parser evaluate                                   # attachment scores
python -m dependency_parser parse the/DET engineer/NOUN trains/VERB    # parse a sentence
```

## Usage

### Command line

```text
$ python -m dependency_parser parse the/DET engineer/NOUN trains/VERB the/DET model/NOUN
Predicted dependencies (dependent -> head : relation):
  the            -> engineer       : det
  engineer       -> trains         : nsubj
  trains         -> ROOT           : root
  the            -> model          : det
  model          -> trains         : dobj
```

The parser recovers the full tree: the determiners attach to their nouns, the subject and
object attach to the verb, and the verb is the sentence root.

### Library

Train on your own grammar or treebank:

```python
from dependency_parser import Parser, TrainingConfig
from dependency_parser.data import train_data

parser = Parser.train(train_data(), TrainingConfig(epochs=10))
parse = parser.parse(train_data()[0])
print(parse.heads, parse.labels)
```

### HTTP service

A standard-library HTTP service trains the parser once at startup and parses sentences:

```bash
python -m dependency_parser serve --port 8000

curl localhost:8000/health
curl -s -X POST localhost:8000/parse \
  -d '{"tokens": [{"form": "the", "pos": "DET"}, {"form": "model", "pos": "NOUN"}, {"form": "runs", "pos": "VERB"}]}'
curl localhost:8000/evaluate
```

See the [operations guide](docs/OPERATIONS.md) for the service contract and constraints. The
service also exposes `GET /ready` (readiness) and `GET /metrics` (per-route request, error,
and latency metrics in Prometheus text format). A production-style stress benchmark
(`uv run python benchmarks/stress.py`) reports throughput and p50/p95/p99 latency; the scaling
path and tradeoffs are in [docs/SCALING.md](docs/SCALING.md) and a full walk-through is in the
[case study](docs/CASE_STUDY.md).

### Demos

Recorded from real runs with [vhs](https://github.com/charmbracelet/vhs); each tape is in `docs/demo/`.

Parsing a tagged sentence into a dependency tree.

<p align="center">
  <img src="docs/demo/parse.gif" alt="Parsing a tagged sentence into a dependency tree" width="860">
</p>

Attachment scores on the held-out set.

<p align="center">
  <img src="docs/demo/evaluate.gif" alt="Attachment scores on the held-out set" width="860">
</p>

The HTTP service parsing a tagged sentence into labeled arcs.

<p align="center">
  <img src="docs/demo/http.gif" alt="The HTTP service parsing a tagged sentence into labeled arcs" width="860">
</p>

## Design decisions

- **Arc-standard transitions with a static oracle.** Linear-time parsing with an exact oracle
  for every projective tree, which keeps training simple and fully supervised.
  ([ADR-0002](docs/adr/0002-arc-standard-oracle.md))
- **An averaged structured perceptron, not a neural policy.** A sparse linear model with
  Collins averaging is transparent, fast to train, and strong on this task.
  ([ADR-0003](docs/adr/0003-averaged-perceptron.md))

## Testing

```bash
make test        # uv run pytest
make coverage    # pytest with an 80% coverage gate, as in CI
make lint type   # ruff format check, ruff lint, mypy
```

- `tests/test_core.py` checks that generated trees are well formed, that the static oracle's
  transition sequence reconstructs the gold tree, legal moves from a configuration, transition
  key round-trips, that the averaged perceptron matches the mean of its post-update weights,
  and that the trained parser assigns a head to every token and reaches a high attachment score.
- `tests/test_service.py` exercises the HTTP handler layer: health and readiness, `/parse` and
  `/evaluate`, rejection of malformed payloads, unknown routes, and recorded metrics.

CI runs ruff format, ruff lint, mypy, and pytest with the coverage gate on Python 3.11 and 3.12,
then builds the package and the Docker image.

## Responsible AI

- **Model card:** [docs/MODEL_CARD.md](docs/MODEL_CARD.md)
- **Data card:** [docs/DATA_CARD.md](docs/DATA_CARD.md)
- **Threat model:** [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)

## Limitations

- The parser is greedy; a beam search or a globally normalized objective would recover some
  of the errors that greedy decoding commits.
- Arc-standard handles projective trees only; non-projective structures need a different
  system such as arc-eager with swap or a graph-based parser.
- The treebank is generated from a grammar rather than annotated by hand, so the vocabulary
  and the construction inventory are illustrative.

## Roadmap

- [ ] Beam search with early update
- [ ] An arc-eager system with the swap transition for non-projective trees
- [ ] Richer features (morphology, distance buckets, label history)

## License

Released under the [MIT License](LICENSE).
