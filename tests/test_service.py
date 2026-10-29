"""Tests for the HTTP service handler (exercised without a socket)."""

from __future__ import annotations

from dependency_parser.service import ParserService, handle


def _service() -> ParserService:
    return ParserService.trained(epochs=5, seed=0)


def test_health_and_ready() -> None:
    service = _service()
    status, payload = handle("GET", "/health", {}, service)
    assert status == 200
    assert "nsubj" in payload["deprels"]
    status, payload = handle("GET", "/ready", {}, service)
    assert status == 200
    assert payload["status"] == "ready"


def test_evaluate_endpoint() -> None:
    service = _service()
    status, payload = handle("GET", "/evaluate", {}, service)
    assert status == 200
    assert payload["uas"] > 0.9
    assert 0.0 <= payload["las"] <= payload["uas"]


def test_parse_endpoint_returns_arcs() -> None:
    service = _service()
    body = {
        "tokens": [
            {"form": "the", "pos": "DET"},
            {"form": "engineer", "pos": "NOUN"},
            {"form": "trains", "pos": "VERB"},
            {"form": "the", "pos": "DET"},
            {"form": "model", "pos": "NOUN"},
        ]
    }
    status, payload = handle("POST", "/parse", body, service)
    assert status == 200
    arcs = payload["arcs"]
    assert len(arcs) == 5
    verb = next(arc for arc in arcs if arc["form"] == "trains")
    assert verb["head"] == 0
    assert verb["deprel"] == "root"


def test_parse_rejects_bad_payloads() -> None:
    service = _service()
    for bad in ([], "nope", [{"form": "x"}], [{"form": "", "pos": "NOUN"}]):
        status, payload = handle("POST", "/parse", {"tokens": bad}, service)
        assert status == 400
        assert "error" in payload


def test_unknown_route() -> None:
    service = _service()
    status, payload = handle("GET", "/nope", {}, service)
    assert status == 404
    assert "error" in payload


def test_metrics_are_recorded() -> None:
    service = _service()
    handle("GET", "/health", {}, service)
    handle("GET", "/nope", {}, service)
    rendered = service.metrics.render_prometheus()
    assert "service_requests_total" in rendered
    assert service.metrics.total_requests >= 2
    assert service.metrics.total_errors >= 1
