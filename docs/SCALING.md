# Scaling - Dependency Parser

This note describes how the parser behaves as load and data grow, and the tradeoffs on the
path to larger deployments.

## Where the time goes
- **Training** is a single pass structure: 10 epochs over 400 sentences, each sentence unrolled
  into about twice its length in transitions, with a constant number of sparse features per
  decision. It completes in roughly one and a half seconds on one core.
- **Decoding** is linear in sentence length: a sentence of *n* tokens takes exactly *2n*
  transitions, each a dot product over a few dozen active features. The parser decodes several
  thousand sentences per second on a single core.

## Request-time scaling
The service is stateless and the parser is pure, so there is no shared mutable state and no
lock on the hot path. A stress benchmark (`uv run python benchmarks/stress.py`) drives the
parse handler under concurrency and reports throughput with p50, p95, and p99 latency. Per
request latency is dominated by the fixed cost of a short sentence, so throughput scales with
the number of worker processes. Horizontal scaling is adding replicas behind a load balancer.

## Data scaling
Training memory is proportional to the number of distinct (feature, transition) weights, which
grows with vocabulary and feature richness, not with corpus size. Larger corpora raise training
time linearly. The two levers are the number of epochs and the feature templates; both trade
accuracy for training cost.

## Tradeoffs on the path to accuracy
- **Greedy versus beam search.** Greedy decoding is fastest and already strong here. A beam
  with early update would recover some errors at a constant-factor cost in latency.
- **Linear model versus neural policy.** A neural policy would raise accuracy on natural text
  but would add a tensor library, automatic differentiation, and accelerator dependencies,
  which this project deliberately avoids.
- **Projective versus non-projective.** Arc-standard is linear time but projective only.
  Supporting non-projective trees means an arc-eager system with swap or a graph-based parser,
  with a higher asymptotic cost.

## Limits
Training is pure Python and single-threaded, which is ideal for learning and modest treebanks
but not for web-scale corpora. The controlled grammar bounds the vocabulary and construction
inventory; scaling to natural text is a data and modeling problem, not a throughput one.
