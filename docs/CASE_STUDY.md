# Case Study - Parsing a sentence end to end

This walk-through follows one sentence through the parser, from tokens to a dependency tree,
and shows where the single hard decision lies.

## The sentence
> a robust system audits the network with the cluster

Tokens and parts of speech:

```
a/DET robust/ADJ system/NOUN audits/VERB the/DET network/NOUN with/ADP the/DET cluster/NOUN
```

## Training
At startup the parser trains on 400 generated projective trees. Each gold tree is unrolled by
the static oracle into a transition sequence, and the averaged perceptron learns to imitate
those decisions. Collins averaging over every update produces the final weights. Training is
deterministic and finishes in roughly one and a half seconds.

## Decoding, step by step
The parser starts with the root on the stack and the nine tokens on the buffer. It then shifts
and attaches:

- `a` and `robust` are attached as a determiner and an adjective of `system` by LEFT arcs.
- `system` is attached as the subject (`nsubj`) of `audits`.
- `audits` becomes the sentence root.
- `the` and `network` form the object noun phrase; `network` attaches to `audits` as `dobj`.
- `with ... cluster` is a prepositional phrase. Here is the one genuinely ambiguous decision:
  `with` can attach to the verb `audits` or to the object `network`.

## The hard decision
Prepositional attachment is the classic source of parsing ambiguity and the only place this
grammar leaves irreducible uncertainty. The treebank makes `with` lean toward noun attachment,
so the trained parser has learned to attach `with` to `network` more often than to `audits`.
It cannot be certain from the tokens alone, and that residual uncertainty is exactly where the
held-out errors concentrate. The parser reaches 0.9879 UAS precisely because it learns the
per-preposition bias and accepts the floor the ambiguity sets, rather than guessing blindly.

## The result
Every unambiguous arc (determiners, adjective, subject, object, root) is recovered correctly,
and the prepositional attachment follows the learned bias. The full tree is returned as a list
of arcs, each with a dependent, a head, and a relation, through the `/parse` endpoint.
