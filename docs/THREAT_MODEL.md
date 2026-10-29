# Threat Model - Dependency Parser

## Assets
- Service availability, the integrity of the trained weights, and predictable resource use.

## Trust boundaries
- The HTTP service accepts untrusted JSON from clients. The training data is trusted and
  generated in-process; there is no external data ingestion at request time.

## Threats and mitigations
- **Resource exhaustion through large inputs.** The `/parse` endpoint bounds the token list to
  a fixed maximum and rejects empty or malformed lists before parsing, so per-request work is
  bounded by a small constant.
- **Malformed requests.** Bodies that are not valid JSON, that omit `tokens`, or whose tokens
  lack a string `form` or `pos` are rejected with a 400 and never reach the parser.
- **Unexpected routes.** Unknown method and path combinations return 404 and are recorded in
  the per-route metrics.
- **Denial of service through concurrency.** The parser is pure and holds no shared mutable
  state across requests, so requests can be served concurrently without contention; a reverse
  proxy should enforce connection and rate limits in production.

## Non-goals
- Authentication, authorization, and transport security are delegated to the deployment
  environment (a reverse proxy or gateway), as described in the operations guide.
