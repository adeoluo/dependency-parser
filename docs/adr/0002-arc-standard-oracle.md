# ADR-0002: Arc-standard transitions with a static oracle

- **Status:** Accepted
- **Date:** 2026-01-01

## Context
Dependency parsing is structured prediction: the output is a tree over the words of a
sentence. Two broad families solve it. Graph-based parsers score every candidate arc and
search for the maximum spanning tree, which is accurate but runs in at least quadratic time
and needs a global inference algorithm. Transition-based parsers reduce parsing to a sequence
of local decisions over a stack and a buffer, which is linear time and maps cleanly onto a
greedy classifier. We want a dependency-free, transparent implementation that trains quickly
and is easy to reason about.

Within the transition-based family, arc-eager and arc-standard are the common systems.
Arc-standard has an especially simple invariant: every transition either shifts a word or
commits a single arc and pops a word, so a sentence of length *n* is parsed in exactly *2n*
transitions. Its static oracle is exact for every projective tree.

## Decision
Implement the **arc-standard** system with three transition families (SHIFT, LEFT, RIGHT) and
a **static oracle**. The oracle prefers LEFT, then RIGHT, then SHIFT, and only allows a RIGHT
attachment once the top stack item has collected all of its gold dependents, which guarantees
that right dependents are never stranded.

## Consequences
- Parsing and training are linear in sentence length and need no global inference.
- The oracle gives a fully supervised signal: every gold tree unrolls into one gold
  transition sequence that the policy learns to imitate.
- Arc-standard handles **projective** trees only. Non-projective structures would require an
  arc-eager system with a swap transition or a graph-based parser; this is recorded as a
  limitation and a roadmap item.
