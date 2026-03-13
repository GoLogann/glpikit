"""Hook definitions for request lifecycle."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

import httpx

RequestHook = Callable[[httpx.Request], None]
ResponseHook = Callable[[httpx.Response], None]
ObservabilityEventHook = Callable[[dict[str, Any]], None]

_SENSITIVE_HEADERS = {
    "authorization",
    "app-token",
    "session-token",
    "x-api-key",
}


@dataclass(slots=True)
class MetricsCollector:
    requests_total: int = 0
    failures_total: int = 0
    by_status: dict[int, int] = field(default_factory=dict)
    by_endpoint: dict[str, int] = field(default_factory=dict)
    by_method: dict[str, int] = field(default_factory=dict)
    latency_ms_sum: float = 0.0
    max_latency_ms: float = 0.0

    def record(
        self,
        *,
        endpoint: str,
        status_code: int,
        method: str | None = None,
        elapsed_ms: float | None = None,
    ) -> None:
        self.requests_total += 1
        if status_code >= 400:
            self.failures_total += 1
        self.by_status[status_code] = self.by_status.get(status_code, 0) + 1
        self.by_endpoint[endpoint] = self.by_endpoint.get(endpoint, 0) + 1
        if method is not None:
            self.by_method[method] = self.by_method.get(method, 0) + 1
        if elapsed_ms is not None:
            self.latency_ms_sum += elapsed_ms
            self.max_latency_ms = max(self.max_latency_ms, elapsed_ms)

    def snapshot(self) -> dict[str, Any]:
        avg_latency = self.latency_ms_sum / self.requests_total if self.requests_total else 0.0
        return {
            "requests_total": self.requests_total,
            "failures_total": self.failures_total,
            "by_status": dict(self.by_status),
            "by_endpoint": dict(self.by_endpoint),
            "by_method": dict(self.by_method),
            "avg_latency_ms": round(avg_latency, 3),
            "max_latency_ms": round(self.max_latency_ms, 3),
        }


def sanitize_headers(headers: httpx.Headers) -> dict[str, str]:
    sanitized: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in _SENSITIVE_HEADERS:
            sanitized[key] = "***"
        else:
            sanitized[key] = value
    return sanitized


def build_observability_hooks(
    *,
    logger: logging.Logger | None = None,
    metrics_collector: MetricsCollector | None = None,
    event_hook: ObservabilityEventHook | None = None,
    enable_tracing: bool = False,
    inject_trace_context: bool = True,
    tracer_name: str = "glpikit.transport",
    correlation_id_header: str = "X-Correlation-ID",
) -> tuple[RequestHook, ResponseHook]:
    active_logger = logger or logging.getLogger("glpikit.transport")
    tracer = None
    propagator = None
    if enable_tracing:
        try:
            from opentelemetry import propagate, trace  # type: ignore

            tracer = trace.get_tracer(tracer_name)
            propagator = propagate
        except Exception:  # pragma: no cover - optional dependency
            tracer = None
            propagator = None

    def on_request(request: httpx.Request) -> None:
        request.headers.setdefault(correlation_id_header, str(uuid.uuid4()))
        request.extensions["glpikit_start_time"] = time.perf_counter()
        request.extensions["glpikit_endpoint"] = request.url.path
        request.extensions["glpikit_method"] = request.method
        request.extensions["glpikit_correlation_id"] = request.headers.get(correlation_id_header)
        if event_hook is not None:
            event_hook(
                {
                    "event": "http_request",
                    "method": request.method,
                    "endpoint": request.url.path,
                    "correlation_id": request.extensions.get("glpikit_correlation_id"),
                }
            )
        if tracer is not None:
            span = tracer.start_span(f"{request.method} {request.url.path}")
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            request.extensions["glpikit_span"] = span
            if inject_trace_context and propagator is not None:
                try:
                    from opentelemetry import trace  # type: ignore

                    propagator.inject(request.headers, context=trace.set_span_in_context(span))
                except Exception:
                    pass
        if active_logger.isEnabledFor(logging.DEBUG):
            active_logger.debug(
                "glpikit.request method=%s url=%s correlation_id=%s headers=%s",
                request.method,
                request.url,
                request.extensions.get("glpikit_correlation_id"),
                sanitize_headers(request.headers),
            )

    def on_response(response: httpx.Response) -> None:
        started = response.request.extensions.get("glpikit_start_time")
        elapsed_ms: float | None = None
        if isinstance(started, float):
            elapsed_ms = (time.perf_counter() - started) * 1000

        endpoint = response.request.extensions.get("glpikit_endpoint", response.request.url.path)
        method = response.request.extensions.get("glpikit_method", response.request.method)
        correlation_id = response.request.extensions.get("glpikit_correlation_id")
        if metrics_collector is not None:
            metrics_collector.record(
                endpoint=str(endpoint),
                status_code=response.status_code,
                method=str(method),
                elapsed_ms=elapsed_ms,
            )

        if event_hook is not None:
            event_hook(
                {
                    "event": "http_response",
                    "method": str(method),
                    "endpoint": str(endpoint),
                    "status_code": response.status_code,
                    "elapsed_ms": elapsed_ms,
                    "correlation_id": correlation_id,
                }
            )

        span = response.request.extensions.get("glpikit_span")
        if span is not None:
            try:
                span.set_attribute("http.status_code", response.status_code)
                if elapsed_ms is not None:
                    span.set_attribute("glpikit.elapsed_ms", elapsed_ms)
                span.end()
            except Exception:  # pragma: no cover - defensive
                pass

        if active_logger.isEnabledFor(logging.DEBUG):
            active_logger.debug(
                "glpikit.response status=%s method=%s url=%s correlation_id=%s elapsed_ms=%s",
                response.status_code,
                response.request.method,
                response.request.url,
                correlation_id,
                f"{elapsed_ms:.2f}" if elapsed_ms is not None else "n/a",
            )

    return on_request, on_response
