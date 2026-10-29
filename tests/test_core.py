"""Tests for the data grammar, transition system, oracle, and parser."""

from __future__ import annotations

from dependency_parser.data import (
    ROOT,
    generate_corpus,
)
from dependency_parser.data import test_data as held_out_data
from dependency_parser.data import train_data as training_data
from dependency_parser.evaluation import evaluate
from dependency_parser.parser import Parser, TrainingConfig
from dependency_parser.transitions import (
    Configuration,
    Move,
    Transition,
    oracle_sequence,
)


def test_generated_trees_are_well_formed() -> None:
    for sentence in generate_corpus(50, seed=3):
        roots = [i for i, token in enumerate(sentence, start=1) if token.head == ROOT]
        assert len(roots) == 1
        for index, token in enumerate(sentence, start=1):
            assert 0 <= token.head <= len(sentence)
            assert token.head != index
            assert token.deprel


def test_oracle_sequence_reconstructs_gold_tree() -> None:
    for sentence in generate_corpus(50, seed=7):
        configuration = Configuration.initial(len(sentence))
        for _, transition in oracle_sequence(sentence):
            configuration.apply(transition)
        assert configuration.is_terminal
        for index, token in enumerate(sentence, start=1):
            assert configuration.heads[index] == token.head
            assert configuration.labels[index] == token.deprel


def test_configuration_legal_moves() -> None:
    configuration = Configuration.initial(2)
    assert configuration.legal() == [Move.SHIFT]
    configuration.apply(Transition(Move.SHIFT))
    configuration.apply(Transition(Move.SHIFT))
    legal = configuration.legal()
    assert Move.SHIFT not in legal
    assert Move.RIGHT in legal


def test_transition_key_roundtrip() -> None:
    assert Transition(Move.SHIFT).key == "shift"
    assert Transition(Move.LEFT, "nsubj").key == "left:nsubj"
    assert Transition(Move.RIGHT, "dobj").key == "right:dobj"


def test_parser_reaches_high_attachment_score() -> None:
    parser = Parser.train(training_data(), TrainingConfig(epochs=5, seed=0))
    report = evaluate(parser, held_out_data())
    assert report.uas > 0.9
    assert report.las > 0.9
    assert report.labeled_correct <= report.unlabeled_correct <= report.tokens


def test_parser_produces_a_head_for_every_token() -> None:
    parser = Parser.train(generate_corpus(80, seed=1), TrainingConfig(epochs=3, seed=0))
    sentence = generate_corpus(1, seed=42)[0]
    parse = parser.parse(sentence)
    assert set(parse.heads) == set(range(1, len(sentence) + 1))
    assert all(0 <= head <= len(sentence) for head in parse.heads.values())
