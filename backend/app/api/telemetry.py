"""Low-cardinality Prometheus metrics and privacy-preserving request logs."""

import json
import logging
import sys
from collections import Counter, defaultdict
from threading import Lock
from time import perf_counter

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

router = APIRouter(tags=["operations"])
logger = logging.getLogger("app.request")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
_LOCK = Lock()
_REQUESTS: Counter[tuple[str, str, int]] = Counter()
_DURATION_SUMS: defaultdict[tuple[str, str], float] = defaultdict(float)
_DURATION_COUNTS: Counter[tuple[str, str]] = Counter()
_DURATION_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
_BUCKET_COUNTS: Counter[tuple[str, str, float]] = Counter()
_ALLOWED_METHODS = {"DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"}


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    return template if isinstance(template, str) else "unmatched"


def _record_request(method: str, route: str, status_code: int, duration: float) -> None:
    safe_method = method if method in _ALLOWED_METHODS else "OTHER"
    safe_status = status_code if 100 <= status_code <= 599 else 500
    key = (safe_method, route, safe_status)
    latency_key = (safe_method, route)
    with _LOCK:
        _REQUESTS[key] += 1
        _DURATION_SUMS[latency_key] += duration
        _DURATION_COUNTS[latency_key] += 1
        for boundary in _DURATION_BUCKETS:
            if duration <= boundary:
                _BUCKET_COUNTS[(*latency_key, boundary)] += 1


def _label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def render_metrics() -> str:
    with _LOCK:
        requests = sorted(_REQUESTS.items())
        sums = dict(_DURATION_SUMS)
        counts = dict(_DURATION_COUNTS)
        buckets = dict(_BUCKET_COUNTS)

    lines = [
        "# HELP app_http_requests_total Completed HTTP requests.",
        "# TYPE app_http_requests_total counter",
    ]
    for (method, route, status_code), count in requests:
        lines.append(
            f'app_http_requests_total{{method="{_label(method)}",route="{_label(route)}",'
            f'status="{status_code}"}} {count}'
        )
    lines.extend(
        [
            "# HELP app_http_request_duration_seconds Request duration in seconds.",
            "# TYPE app_http_request_duration_seconds histogram",
        ]
    )
    for method, route in sorted(counts):
        label_prefix = f'method="{_label(method)}",route="{_label(route)}"'
        for boundary in _DURATION_BUCKETS:
            count = buckets.get((method, route, boundary), 0)
            lines.append(
                f'app_http_request_duration_seconds_bucket{{{label_prefix},'
                f'le="{boundary}"}} {count}'
            )
        lines.append(
            f'app_http_request_duration_seconds_bucket{{{label_prefix},le="+Inf"}} '
            f'{counts[(method, route)]}'
        )
        lines.append(
            f"app_http_request_duration_seconds_sum{{{label_prefix}}} "
            f"{sums[(method, route)]}"
        )
        lines.append(
            f"app_http_request_duration_seconds_count{{{label_prefix}}} "
            f"{counts[(method, route)]}"
        )
    return "\n".join(lines) + "\n"


@router.get("/metrics", include_in_schema=False)
def metrics() -> PlainTextResponse:
    return PlainTextResponse(
        render_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )


async def observe_request(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    started = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = perf_counter() - started
        route = _route_template(request)
        _record_request(request.method, route, status_code, duration)
        logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "method": request.method
                    if request.method in _ALLOWED_METHODS
                    else "OTHER",
                    "route": route,
                    "status": status_code,
                    "duration_ms": round(duration * 1000, 2),
                },
                separators=(",", ":"),
            )
        )
