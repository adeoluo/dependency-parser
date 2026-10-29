# Model / System Card - Dependency Parser

## Overview
- **What it is:** an arc-standard, transition-based dependency parser with an averaged
  structured perceptron policy, implemented from scratch with zero runtime dependencies.
- **Base model(s):** from-scratch; no pretrained components.
- **Version and date:** 1.0, 2026-01-01.

## Intended use
- **Primary use cases:** teaching and demonstrating transition-based parsing, the arc-standard
  oracle, and the averaged perceptron; a reference implementation for experiments on features
  and decoding.
- **Primary users:** engineers and researchers studying structured prediction and parsing.

## Out-of-scope / prohibited use
- Production parsing of open-domain natural language. The parser is trained on a controlled
  grammar and handles projective trees only, so it should not be relied on for arbitrary text.

## Performance
- Held-out **UAS 0.9879** and **LAS 0.9879** over 663 tokens, against a left-branching baseline
  of 0.0558. See [`EVALUATION_REPORT.md`](EVALUATION_REPORT.md). Residual errors are
  concentrated on genuinely ambiguous prepositional attachments.

## Risks and limitations
- Greedy decoding commits to each transition and cannot revise earlier mistakes.
- Arc-standard cannot represent non-projective trees.
- Results are on a generated grammar and will not transfer directly to natural corpora.

## Safety mitigations
- The HTTP service validates that the token list is non-empty, within a fixed length bound,
  and that each token carries a string form and part of speech, before any parsing runs.

## Environmental / cost footprint
- Training takes roughly one to two seconds of single-core CPU time with no accelerator, so the
  energy footprint is negligible.
