"""Command line interface for the dependency parser."""

from __future__ import annotations

import argparse

from dependency_parser.data import Token, test_data, train_data
from dependency_parser.evaluation import evaluate
from dependency_parser.parser import Parser, TrainingConfig


def _train(epochs: int, seed: int) -> Parser:
    return Parser.train(train_data(), TrainingConfig(epochs=epochs, seed=seed))


def _cmd_evaluate(args: argparse.Namespace) -> None:
    parser = _train(args.epochs, args.seed)
    report = evaluate(parser, test_data())
    print("Attachment scores on the held-out treebank:")
    print(f"  {report.format()}")


def _parse_token_specs(specs: list[str]) -> list[Token]:
    tokens: list[Token] = []
    for spec in specs:
        form, _, pos = spec.rpartition("/")
        if not form or not pos:
            raise SystemExit(f"token '{spec}' must be written as form/POS, for example model/NOUN")
        tokens.append(Token(form=form, pos=pos.upper(), head=-1, deprel=""))
    return tokens


def _cmd_parse(args: argparse.Namespace) -> None:
    parser = _train(args.epochs, args.seed)
    sentence = _parse_token_specs(args.tokens)
    parse = parser.parse(sentence)
    print("Predicted dependencies (dependent -> head : relation):")
    for index, token in enumerate(sentence, start=1):
        head = parse.heads[index]
        head_form = "ROOT" if head == 0 else sentence[head - 1].form
        print(f"  {token.form:<14} -> {head_form:<14} : {parse.labels[index]}")


def _cmd_serve(args: argparse.Namespace) -> None:
    from dependency_parser.service import serve

    serve(host=args.host, port=args.port)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="dependency-parser", description=__doc__)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--seed", type=int, default=0)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("evaluate", help="unlabeled and labeled attachment scores on held-out data")

    parse = sub.add_parser("parse", help="parse a sentence given as form/POS tokens")
    parse.add_argument("tokens", nargs="+", help="whitespace-separated form/POS tokens")

    serve = sub.add_parser("serve", help="start the HTTP parsing service")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    handlers = {"evaluate": _cmd_evaluate, "parse": _cmd_parse, "serve": _cmd_serve}
    args = parser.parse_args(argv)
    handlers[args.command](args)


if __name__ == "__main__":
    main()
