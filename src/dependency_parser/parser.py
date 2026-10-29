"""The greedy transition based parser: training loop and decoding."""

from __future__ import annotations

from dataclasses import dataclass, field

from dependency_parser.data import ROOT, Sentence, deprels
from dependency_parser.features import extract
from dependency_parser.perceptron import AveragedPerceptron
from dependency_parser.transitions import (
    Configuration,
    Move,
    Transition,
    oracle_sequence,
)


@dataclass(frozen=True)
class TrainingConfig:
    """Training hyperparameters."""

    epochs: int = 10
    seed: int = 0


@dataclass
class Parse:
    """A decoded dependency tree: a head and a relation for each one based token."""

    heads: dict[int, int] = field(default_factory=dict)
    labels: dict[int, str] = field(default_factory=dict)


def _candidate_actions(moves: list[Move], labels: tuple[str, ...]) -> list[str]:
    actions: list[str] = []
    for move in moves:
        if move is Move.SHIFT:
            actions.append("shift")
        elif move is Move.LEFT:
            actions.extend(f"left:{label}" for label in labels)
        else:
            actions.extend(f"right:{label}" for label in labels)
    return actions


def _decode(action: str) -> Transition:
    if action == "shift":
        return Transition(Move.SHIFT)
    name, label = action.split(":", 1)
    return Transition(Move.LEFT if name == "left" else Move.RIGHT, label)


@dataclass
class Parser:
    """An averaged perceptron policy over arc-standard transitions."""

    model: AveragedPerceptron
    labels: tuple[str, ...]

    @classmethod
    def train(cls, sentences: list[Sentence], config: TrainingConfig) -> Parser:
        import random

        labels = deprels()
        model = AveragedPerceptron()
        rng = random.Random(config.seed)
        order = list(sentences)
        for _ in range(config.epochs):
            rng.shuffle(order)
            for sentence in order:
                for configuration, gold in oracle_sequence(sentence):
                    features = extract(configuration, sentence)
                    actions = _candidate_actions(configuration.legal(), labels)
                    predicted = model.predict(features, actions)
                    model.update(features, predicted, gold.key)
        model.finalize()
        return cls(model=model, labels=labels)

    def parse(self, sentence: Sentence) -> Parse:
        configuration = Configuration.initial(len(sentence))
        while not configuration.is_terminal:
            features = extract(configuration, sentence)
            actions = _candidate_actions(configuration.legal(), self.labels)
            action = self.model.predict(features, actions)
            configuration.apply(_decode(action))
        heads = {
            index: configuration.heads.get(index, ROOT) for index in range(1, len(sentence) + 1)
        }
        labels = {
            index: configuration.labels.get(index, "dep") for index in range(1, len(sentence) + 1)
        }
        return Parse(heads=heads, labels=labels)
