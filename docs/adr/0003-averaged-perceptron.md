# ADR-0003: An averaged structured perceptron policy

- **Status:** Accepted
- **Date:** 2026-01-01

## Context
The transition system needs a policy that, at each configuration, chooses the next transition.
The policy is a multi-class classifier over transitions whose inputs are features of the stack
and buffer. Options range from a neural network (accurate, but it would pull in a tensor
library and automatic differentiation) to a log-linear model trained by gradient methods, to
the structured perceptron. We want strong accuracy with zero runtime dependencies and fully
transparent training.

## Decision
Use an **averaged structured perceptron** over sparse string features. Training follows the
oracle transition sequence with teacher forcing: at each decision the highest-scoring legal
transition is compared with the oracle transition, and on a mistake the active features have
their weight for the oracle transition increased and for the predicted transition decreased.
Collins-style **weight averaging** is applied with per-key update timestamps so the final
model is the mean of every intermediate weight vector, computed lazily in one pass.

## Consequences
- The learner is a few dozen lines, has no dependencies, and is easy to inspect: a weight is a
  plain number keyed by a (feature, transition) pair.
- Averaging markedly reduces variance and is the difference between an unstable perceptron and
  a competitive parser.
- Teacher forcing means the policy only ever sees configurations on the gold path; a beam
  search with early update would expose it to its own mistakes and is recorded as a roadmap
  item.
