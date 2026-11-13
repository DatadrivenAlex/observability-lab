"""A deliberately small API for exploring local observability."""
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest
from opentelemetry import trace

log = logging.getLogger("observability_lab")
logging.basicConfig(level=logging.INFO, format="%(message)s")
requests_total = Counter("lab_http_requests_total", "HTTP requests by route and status", ["method", "route", "status"])
latency = Histogram("lab_http_request_duration_seconds", "Request duration by route", ["method", "route"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Opt-in: local tests and standalone runs don't require a collector.
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        provider = TracerProvider(resource=Resource.create({"service.name": "observability-lab"}))
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(provider)
        app.state.tracer_provider = provider
    yield
    if hasattr(app.state, "tracer_provider"):
        app.state.tracer_provider.shutdown()

app = FastAPI(title="Observability Lab", lifespan=lifespan)
# Install instrumentation before startup so incoming HTTP requests receive trace spans.
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app, excluded_urls="metrics,healthz")

@app.middleware("http")
async def observe(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))[:128]
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["x-request-id"] = request_id
        return response
    finally:
        route = getattr(request.scope.get("route"), "path", "unmatched")
        duration = time.perf_counter() - start
        if route not in ("/metrics", "/healthz"):
            requests_total.labels(request.method, route, str(status)).inc()
            latency.labels(request.method, route).observe(duration)
            context = trace.get_current_span().get_span_context()
            log.info(json.dumps({"event": "http_request", "method": request.method, "route": route, "status": status, "duration_ms": round(duration * 1000, 2), "request_id": request_id, "trace_id": format(context.trace_id, "032x") if context.is_valid else None}))

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/work")
def work(fail: bool = False):
    if fail:
        raise HTTPException(status_code=503, detail="simulated failure")
    return {"result": "ok"}
