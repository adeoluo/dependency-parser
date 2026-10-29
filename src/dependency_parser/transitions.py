"""The arc-standard transition system and its static oracle.

The arc-standard system (Nivre, 2004) parses a sentence by manipulating a stack
and a buffer. A configuration is a triple of a stack, a buffer, and the set of
arcs committed so far. Three transition families drive it:

``SHIFT``        move the front of the buffer onto the stack.
``LEFT(label)``  attach the second stack item as a ``label`` dependent of the top
                 item, then pop the second item.
``RIGHT(label)`` attach the top stack item as a ``label`` dependent of the second
                 item, then pop the top item.

A static oracle maps a gold tree to the unique transition sequence that builds it,
which supplies the supervised training signal for the perceptron policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from dependency_parser.data import ROOT, Sentence


class Move(Enum):
    """The three arc-standard transition families."""

    SHIFT = "shift"
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True)
class Transition:
    """A move paired with a dependency label (empty for ``SHIFT``)."""

    move: Move
    label: str = ""

    @property
    def key(self) -> str:
        return self.move.value if self.move is Move.SHIFT else f"{self.move.value}:{self.label}"


@dataclass
class Configuration:
    """A mutable arc-standard configuration over a sentence of ``length`` tokens."""

    length: int
    stack: list[int] = field(default_factory=lambda: [ROOT])
    buffer: list[int] = field(default_factory=list)
    heads: dict[int, int] = field(default_factory=dict)
    labels: dict[int, str] = field(default_factory=dict)

    @classmethod
    def initial(cls, length: int) -> Configuration:
        return cls(length=length, stack=[ROOT], buffer=list(range(1, length + 1)))

    @property
    def is_terminal(self) -> bool:
        return not self.buffer and len(self.stack) == 1

    def legal(self) -> list[Move]:
        moves: list[Move] = []
        if self.buffer:
            moves.append(Move.SHIFT)
        if len(self.stack) >= 2:
            if self.stack[-2] != ROOT:
                moves.append(Move.LEFT)
            moves.append(Move.RIGHT)
        return moves

    def apply(self, transition: Transition) -> None:
        if transition.move is Move.SHIFT:
            self.stack.append(self.buffer.pop(0))
            return
        top = self.stack[-1]
        second = self.stack[-2]
        if transition.move is Move.LEFT:
            self.heads[second] = top
            self.labels[second] = transition.label
            del self.stack[-2]
        else:
            self.heads[top] = second
            self.labels[top] = transition.label
            self.stack.pop()


def _gold_dependents(sentence: Sentence) -> dict[int, set[int]]:
    dependents: dict[int, set[int]] = {}
    for index, token in enumerate(sentence, start=1):
        dependents.setdefault(token.head, set()).add(index)
    return dependents


def oracle(configuration: Configuration, sentence: Sentence) -> Transition:
    """Return the gold transition for ``configuration`` given the gold ``sentence``.

    Preference order is ``LEFT`` then ``RIGHT`` then ``SHIFT``. ``RIGHT`` only
    fires once the top item has collected every gold dependent, otherwise those
    right dependents could never attach after the item is popped.
    """

    dependents = _gold_dependents(sentence)
    if len(configuration.stack) >= 2:
        top = configuration.stack[-1]
        second = configuration.stack[-2]
        if second != ROOT and sentence[second - 1].head == top:
            return Transition(Move.LEFT, sentence[second - 1].deprel)
        if sentence[top - 1].head == second:
            attached = dependents.get(top, set())
            if attached <= set(configuration.heads):
                return Transition(Move.RIGHT, sentence[top - 1].deprel)
    return Transition(Move.SHIFT)


def oracle_sequence(sentence: Sentence) -> list[tuple[Configuration, Transition]]:
    """Unroll the static oracle into (configuration snapshot, transition) steps.

    The yielded configuration is a shallow copy taken *before* the transition is
    applied, so callers can extract features from the exact decision point.
    """

    configuration = Configuration.initial(len(sentence))
    steps: list[tuple[Configuration, Transition]] = []
    while not configuration.is_terminal:
        transition = oracle(configuration, sentence)
        snapshot = Configuration(
            length=configuration.length,
            stack=list(configuration.stack),
            buffer=list(configuration.buffer),
            heads=dict(configuration.heads),
            labels=dict(configuration.labels),
        )
        steps.append((snapshot, transition))
        configuration.apply(transition)
    return steps
