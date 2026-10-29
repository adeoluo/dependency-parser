# Data Card - Dependency Parser

## Sources and provenance
The treebank is **generated**, not collected. A small dependency grammar in
`src/dependency_parser/data.py` composes projective trees from fixed vocabularies of
determiners, adjectives, nouns, transitive and intransitive verbs, and prepositions. Because
each tree is assembled by attaching well-formed phrases, the gold heads and relations are
correct by construction. The training split is drawn from seed 1 (400 sentences) and the
held-out split from seed 9999 (100 sentences), so the two splits are disjoint and reproducible.

## Licensing
The grammar and vocabularies are original to this project and carry the repository's MIT
license. No external corpus is used, so there are no third-party redistribution terms.

## Composition
Each sentence is a list of tokens with a surface form, a coarse part of speech (DET, ADJ,
NOUN, VERB, ADP), a one-based head index (zero is the artificial root), and a dependency
relation drawn from a fixed inventory (root, nsubj, dobj, det, amod, prep, pobj). Sentences
range from three to roughly nine tokens. The language is a small controlled subset of English.

## Preprocessing and filtering
None is required: the generator emits clean, fully labeled trees. There is no personally
identifiable information and no free text to clean.

## Contamination checks
Training and evaluation use disjoint seeds. Because generation is deterministic, any overlap
would be visible and reproducible; the seed separation keeps the held-out set independent.

## Known biases and gaps
The vocabulary and the construction inventory are deliberately small and skew toward an
engineering domain. Prepositional attachment is intentionally ambiguous: some prepositions
lean toward noun attachment and others toward verb attachment, with an irreducible residue.
The treebank contains projective trees only.

## Ethical considerations
The data is synthetic and contains no personal or sensitive content, so consent and privacy
do not apply. The main risk is over-generalizing results from a controlled grammar to natural
text, which the model card and README call out explicitly.
