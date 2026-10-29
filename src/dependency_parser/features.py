"""Feature templates over an arc-standard configuration.

Features are plain strings in the Zhang and Nivre tradition: the word forms and
parts of speech of the top stack items and the front buffer items, plus a few
conjunctions that let the linear policy capture simple word-order regularities.
Each active feature is scored against every candidate transition by the
perceptron, so the feature extractor only needs to enumerate the active strings.
"""

from __future__ import annotations

from dependency_parser.data import ROOT, Sentence
from dependency_parser.transitions import Configuration

_NONE = "__none__"
_ROOT = "__root__"


def _form(sentence: Sentence, index: int | None) -> str:
    if index is None:
        return _NONE
    if index == ROOT:
        return _ROOT
    return sentence[index - 1].form


def _pos(sentence: Sentence, index: int | None) -> str:
    if index is None:
        return _NONE
    if index == ROOT:
        return _ROOT
    return sentence[index - 1].pos


def _at(items: list[int], offset: int) -> int | None:
    return items[offset] if 0 <= offset < len(items) else None


def extract(configuration: Configuration, sentence: Sentence) -> list[str]:
    """Return the active feature strings for a parser decision point."""

    s1 = _at(configuration.stack, len(configuration.stack) - 1)
    s2 = _at(configuration.stack, len(configuration.stack) - 2)
    s3 = _at(configuration.stack, len(configuration.stack) - 3)
    b1 = _at(configuration.buffer, 0)
    b2 = _at(configuration.buffer, 1)
    b3 = _at(configuration.buffer, 2)

    s1w, s1t = _form(sentence, s1), _pos(sentence, s1)
    s2w, s2t = _form(sentence, s2), _pos(sentence, s2)
    s3t = _pos(sentence, s3)
    b1w, b1t = _form(sentence, b1), _pos(sentence, b1)
    b2t = _pos(sentence, b2)
    b3t = _pos(sentence, b3)

    features = [
        "bias",
        f"s1w={s1w}",
        f"s1t={s1t}",
        f"s1wt={s1w}/{s1t}",
        f"s2w={s2w}",
        f"s2t={s2t}",
        f"s2wt={s2w}/{s2t}",
        f"s3t={s3t}",
        f"b1w={b1w}",
        f"b1t={b1t}",
        f"b1wt={b1w}/{b1t}",
        f"b2t={b2t}",
        f"b3t={b3t}",
        f"s1t.s2t={s1t}/{s2t}",
        f"s1w.s2w={s1w}/{s2w}",
        f"s1t.b1t={s1t}/{b1t}",
        f"s2t.b1t={s2t}/{b1t}",
        f"s1w.b1w={s1w}/{b1w}",
        f"s1t.b1t.b2t={s1t}/{b1t}/{b2t}",
        f"s2t.s1t.b1t={s2t}/{s1t}/{b1t}",
        f"s1wt.s2t={s1w}/{s1t}/{s2t}",
        f"s2wt.s1t={s2w}/{s2t}/{s1t}",
        f"dist={min(abs((s1 or 0) - (s2 or 0)), 8) if s1 and s2 else 0}",
    ]
    return features
