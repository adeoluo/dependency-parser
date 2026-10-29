"""A deterministic, projective dependency treebank generated from a known grammar.

Hand annotating head indices is error prone, so instead this module *generates*
projective dependency trees from a small dependency grammar. Because every tree
is produced by composing well formed phrases, the gold heads and relations are
correct by construction. This yields an arbitrarily large, perfectly consistent
treebank that is reproducible from a seed, which is ideal for exercising a
transition based parser without pulling in an external corpus.

Each sentence is a list of :class:`Token` with one based positions; the artificial
ROOT lives at position ``0`` and is never materialised as a token. A token whose
``head`` is ``0`` is the syntactic root of the sentence (always the main verb).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

ROOT = 0


@dataclass(frozen=True)
class Token:
    """One word with its part of speech and its gold dependency."""

    form: str
    pos: str
    head: int
    deprel: str


Sentence = list[Token]

_DETERMINERS: tuple[str, ...] = ("the", "a", "that", "this", "some", "each", "every")
_ADJECTIVES: tuple[str, ...] = (
    "small",
    "large",
    "quiet",
    "bright",
    "sturdy",
    "ancient",
    "clever",
    "distant",
    "robust",
    "scalable",
)
_NOUNS: tuple[str, ...] = (
    "engineer",
    "model",
    "dataset",
    "server",
    "agent",
    "system",
    "report",
    "network",
    "student",
    "algorithm",
    "pipeline",
    "cluster",
)
_TRANSITIVE_VERBS: tuple[str, ...] = (
    "trains",
    "evaluates",
    "builds",
    "audits",
    "deploys",
    "inspects",
    "optimizes",
    "monitors",
)
_INTRANSITIVE_VERBS: tuple[str, ...] = (
    "runs",
    "fails",
    "improves",
    "scales",
    "converges",
)
_PREPOSITIONS: tuple[str, ...] = ("on", "with", "near", "under", "across", "within")

# Prepositional attachment is the classic source of parsing ambiguity: a phrase
# such as "audits the server with the network" can attach "with" to the verb or
# to the object noun. These biases make some prepositions lean toward noun
# attachment and others toward verb attachment, while leaving a residue of
# genuinely ambiguous cases that no amount of training data can resolve from the
# observable tokens alone. A competent parser should learn the bias and accept
# the irreducible remainder.
_NOUN_ATTACH_BIAS: dict[str, float] = {
    "with": 0.75,
    "on": 0.7,
    "near": 0.6,
    "under": 0.4,
    "across": 0.3,
    "within": 0.25,
}


class _Builder:
    """Accumulates tokens in linear order and resolves heads by position."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng
        self._forms: list[str] = []
        self._pos: list[str] = []
        self._head: list[int] = []
        self._deprel: list[str] = []

    def _add(self, form: str, pos: str) -> int:
        self._forms.append(form)
        self._pos.append(pos)
        self._head.append(-1)
        self._deprel.append("")
        return len(self._forms)

    def _attach(self, position: int, head: int, deprel: str) -> None:
        self._head[position - 1] = head
        self._deprel[position - 1] = deprel

    def _noun_phrase(self) -> int:
        determiner: int | None = None
        if self._rng.random() < 0.8:
            determiner = self._add(self._rng.choice(_DETERMINERS), "DET")
        adjectives: list[int] = []
        for _ in range(self._rng.choice((0, 0, 1, 1, 2))):
            adjectives.append(self._add(self._rng.choice(_ADJECTIVES), "ADJ"))
        noun = self._add(self._rng.choice(_NOUNS), "NOUN")
        if determiner is not None:
            self._attach(determiner, noun, "det")
        for adjective in adjectives:
            self._attach(adjective, noun, "amod")
        return noun

    def sentence(self) -> Sentence:
        transitive = self._rng.random() < 0.7
        subject = self._noun_phrase()
        verbs = _TRANSITIVE_VERBS if transitive else _INTRANSITIVE_VERBS
        verb = self._add(self._rng.choice(verbs), "VERB")
        self._attach(verb, ROOT, "root")
        self._attach(subject, verb, "nsubj")
        obj: int | None = None
        if transitive and self._rng.random() < 0.85:
            obj = self._noun_phrase()
            self._attach(obj, verb, "dobj")
        if self._rng.random() < 0.6:
            preposition_form = self._rng.choice(_PREPOSITIONS)
            preposition = self._add(preposition_form, "ADP")
            prepositional_object = self._noun_phrase()
            attach_to_noun = obj is not None and self._rng.random() < _NOUN_ATTACH_BIAS.get(
                preposition_form, 0.5
            )
            head = obj if (attach_to_noun and obj is not None) else verb
            self._attach(preposition, head, "prep")
            self._attach(prepositional_object, preposition, "pobj")
        return [
            Token(form=self._forms[i], pos=self._pos[i], head=self._head[i], deprel=self._deprel[i])
            for i in range(len(self._forms))
        ]


def generate_corpus(count: int, *, seed: int) -> list[Sentence]:
    """Generate ``count`` projective dependency trees deterministically from ``seed``."""

    rng = random.Random(seed)
    return [_Builder(rng).sentence() for _ in range(count)]


def train_data() -> list[Sentence]:
    """A reproducible training treebank."""

    return generate_corpus(400, seed=1)


def test_data() -> list[Sentence]:
    """A reproducible held-out treebank drawn from a disjoint seed."""

    return generate_corpus(100, seed=9999)


def deprels() -> tuple[str, ...]:
    """The fixed inventory of dependency relations used by the grammar."""

    return ("root", "nsubj", "dobj", "det", "amod", "prep", "pobj")
