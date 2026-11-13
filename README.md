# Observability Lab

A newly created portfolio demonstration of a FastAPI service with structured request logs, Prometheus metrics and alert rules, an OpenTelemetry trace pipeline to Jaeger, and a Grafana dashboard. This is a local lab, not a historical production deployment or claim of prior professional experience.

## Run locally

Requires Docker and Docker Compose. Run `docker compose up --build`. The API, Prometheus, Grafana and Jaeger UIs are bound to localhost only.

- API: http://localhost:8000/docs
- Prometheus targets and alert rules: http://localhost:9090/targets and http://localhost:9090/alerts
- Grafana: http://localhost:3000 (admin / local-demo-only; for local demo only)
- Jaeger: http://localhost:16686 (search service `observability-lab`)

Create requests and errors: `for i in $(seq 1 25); do curl -s 'http://localhost:8000/work?fail=true' >/dev/null; done`. Metrics and alert rules need scrape/evaluation time; the `for` duration is 30 seconds. Inspect logs via `docker compose logs api` and search traces in Jaeger. Alert rules appear in Prometheus; no alert notification receiver is configured.

Stop and remove the stack with `docker compose down`. The demo password is not suitable for any exposed environment; never use these settings in production. No external deployment is included.

## Tests

Run `uv run --group dev pytest -q`. The API tests cover health, request ID propagation, simulated failures and generated metrics. Docker Compose end-to-end behavior is environment-dependent and must be checked separately.
