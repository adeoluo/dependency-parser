"""A dependency-free HTTP service exposing the trained dependency parser.

The service trains the parser once at startup over the bundled treebank and then
parses submitted sentences and reports held-out attachment scores. A pure handler
is separated from the socket binding so it can be tested without a network.

Endpoints
---------
``GET  /health``    liveness and the dependency-relation inventory.
``GET  /ready``     readiness once the parser is trained.
``GET  /metrics``   per-route request, error, and latency metrics (Prometheus text).
``POST /parse``     body ``{"tokens": [{"form": str, "pos": str}]}``; returns arcs.
``GET  /evaluate``  unlabeled and labeled attachment scores on held-out data.
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from dependency_parser.data import Token, deprels, test_data, train_data
from dependency_parser.evaluation import evaluate
from dependency_parser.observability import ServiceMetrics
from dependency_parser.parser import Parser, TrainingConfig

JsonObject = dict[str, Any]
_MAX_TOKENS = 100


@dataclass(frozen=True)
class ParserService:
    """Holds the trained parser and answers parse and evaluation requests."""

    parser: Parser
    metrics: ServiceMetrics = field(default_factory=ServiceMetrics)

    @classmethod
    def trained(cls, *, epochs: int = 10, seed: int = 0) -> ParserService:
        parser = Parser.train(train_data(), TrainingConfig(epochs=epochs, seed=seed))
        return cls(parser=parser)

    def parse(self, tokens: list[dict[str, str]]) -> JsonObject:
        sentence = [
            Token(form=token["form"], pos=token["pos"].upper(), head=-1, deprel="")
            for token in tokens
        ]
        parse = self.parser.parse(sentence)
        arcs = []
        for index, token in enumerate(sentence, start=1):
            head = parse.heads[index]
            arcs.append(
                {
                    "index": index,
                    "form": token.form,
                    "pos": token.pos,
                    "head": head,
                    "head_form": "ROOT" if head == 0 else sentence[head - 1].form,
                    "deprel": parse.labels[index],
                }
            )
        return {"tokens": [t.form for t in sentence], "arcs": arcs}

    def evaluate(self) -> JsonObject:
        report = evaluate(self.parser, test_data())
        return {
            "uas": round(report.uas, 6),
            "las": round(report.las, 6),
            "tokens": report.tokens,
        }


def _valid_tokens(value: Any) -> list[dict[str, str]] | None:
    if not isinstance(value, list) or not value or len(value) > _MAX_TOKENS:
        return None
    tokens: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            return None
        form = item.get("form")
        pos = item.get("pos")
        if not isinstance(form, str) or not isinstance(pos, str) or not form or not pos:
            return None
        tokens.append({"form": form, "pos": pos})
    return tokens


def _route(
    method: str, path: str, body: Mapping[str, Any], service: ParserService
) -> tuple[int, JsonObject]:
    if method == "GET" and path == "/health":
        return 200, {"status": "ok", "deprels": list(deprels())}
    if method == "GET" and path == "/evaluate":
        return 200, service.evaluate()
    if method == "POST" and path == "/parse":
        tokens = _valid_tokens(body.get("tokens"))
        if tokens is None:
            return 400, {
                "error": (
                    "'tokens' must be a non-empty list of "
                    f"at most {_MAX_TOKENS} objects with 'form' and 'pos'"
                )
            }
        return 200, service.parse(tokens)
    return 404, {"error": f"no route for {method} {path}"}


def handle(
    method: str, path: str, body: Mapping[str, Any], service: ParserService
) -> tuple[int, JsonObject]:
    """Route a request, recording per-route metrics, and return status and payload."""

    if method == "GET" and path == "/ready":
        return 200, {"status": "ready", "deprels": list(deprels())}
    start = time.perf_counter()
    status, payload = _route(method, path, body, service)
    service.metrics.observe(
        f"{method} {path}", (time.perf_counter() - start) * 1000.0, error=status >= 400
    )
    return status, payload


class _Handler(BaseHTTPRequestHandler):  # pragma: no cover - exercised over sockets
    service: ParserService

    def _respond(self, status: int, payload: JsonObject) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/metrics":
            body = self.service.metrics.render_prometheus().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        status, payload = handle("GET", self.path, {}, self.service)
        self._respond(status, payload)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._respond(400, {"error": "request body is not valid JSON"})
            return
        status, payload = handle("POST", self.path, body, self.service)
        self._respond(status, payload)

    def log_message(self, *_: Any) -> None:
        return


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover
    """Start the HTTP service (blocking)."""

    handler = type("_BoundHandler", (_Handler,), {"service": ParserService.trained()})
    server = ThreadingHTTPServer((host, port), handler)
    print(f"dependency-parser service listening on http://{host}:{port}")
    server.serve_forever()
