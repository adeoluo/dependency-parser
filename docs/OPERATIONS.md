# Operations Guide - Dependency Parser

The service is a single stateless process that trains the parser once at startup and then
answers parse and evaluation requests. It has zero runtime dependencies and binds only the
Python standard library HTTP server.

## Service contract

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/health` | none | `{"status": "ok", "deprels": [...]}` |
| GET | `/ready` | none | `{"status": "ready", "deprels": [...]}` once trained |
| GET | `/metrics` | none | Prometheus text: per-route requests, errors, latency histogram |
| POST | `/parse` | `{"tokens": [{"form": str, "pos": str}]}` | arcs with head, head form, and relation |
| GET | `/evaluate` | none | `{"uas": float, "las": float, "tokens": int}` |

## Startup
Training runs once when the process starts and takes roughly one to two seconds. Until it
completes the process is not listening, so a readiness probe against `/ready` will fail closed.
There is no warm-up traffic requirement: the first request is served at full speed.

## Constraints and limits
- The `/parse` token list is bounded to 100 tokens. Larger lists are rejected with a 400.
- Each token must provide a non-empty string `form` and `pos`; anything else is a 400.
- Request bodies that are not valid JSON return a 400 without touching the parser.

## Observability
- `/metrics` exposes `service_requests_total`, `service_errors_total`,
  `service_request_duration_ms_sum`, and a latency histogram, all labeled by route.
- Scrape `/metrics` with Prometheus and alert on error rate and p99 latency per route.

## Health and readiness
- **Liveness:** `/health` returns as soon as the process is up.
- **Readiness:** `/ready` returns ready only after training completes. Wire it to the
  orchestrator readiness probe so traffic is withheld until the parser is loaded.

## Failure modes and responses
- **Malformed or oversized input:** rejected with a 400 and counted as a route error.
- **Unknown route:** 404, counted in metrics.
- **Process restart:** safe at any time; the parser is rebuilt deterministically from the
  bundled grammar, so restarts produce identical weights.

## Deployment
Run the container from the provided `Dockerfile` behind a reverse proxy that terminates TLS and
enforces connection and rate limits. The process is stateless, so scaling out is a matter of
running more replicas behind a load balancer (see [SCALING.md](SCALING.md)).
