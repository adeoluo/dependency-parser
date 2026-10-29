"""Attachment-score evaluation for the dependency parser."""

from __future__ import annotations

from dataclasses import dataclass

from dependency_parser.data import Sentence
from dependency_parser.parser import Parser


@dataclass(frozen=True)
class AttachmentReport:
    """Unlabeled and labeled attachment scores over a treebank."""

    tokens: int
    unlabeled_correct: int
    labeled_correct: int

    @property
    def uas(self) -> float:
        return self.unlabeled_correct / self.tokens if self.tokens else 0.0

    @property
    def las(self) -> float:
        return self.labeled_correct / self.tokens if self.tokens else 0.0

    def format(self) -> str:
        return (
            f"UAS={self.uas:.4f}  LAS={self.las:.4f}  "
            f"(tokens={self.tokens}, head-correct={self.unlabeled_correct}, "
            f"head+label-correct={self.labeled_correct})"
        )


def evaluate(parser: Parser, sentences: list[Sentence]) -> AttachmentReport:
    """Score a parser against a gold treebank, excluding the artificial root."""

    tokens = 0
    unlabeled = 0
    labeled = 0
    for sentence in sentences:
        parse = parser.parse(sentence)
        for index, token in enumerate(sentence, start=1):
            tokens += 1
            head_ok = parse.heads.get(index) == token.head
            if head_ok:
                unlabeled += 1
                if parse.labels.get(index) == token.deprel:
                    labeled += 1
    return AttachmentReport(tokens=tokens, unlabeled_correct=unlabeled, labeled_correct=labeled)
