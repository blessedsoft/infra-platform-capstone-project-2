"""Small HTTP service used by gateway, catalog, and orders."""

import json
import logging
import os
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


SERVICE = os.getenv("SERVICE_NAME", "gateway")
PORT = int(os.getenv("PORT", "8080"))
CATALOG_URL = os.getenv("CATALOG_URL", "http://catalog:8080")
ORDERS_URL = os.getenv("ORDERS_URL", "http://orders:8080")
REQUESTS = 0
ERRORS = 0
REQUEST_SECONDS = 0.0
DURATION_BUCKETS = {0.1: 0, 0.5: 0, 1.0: 0, 5.0: 0, float("inf"): 0}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "level": record.levelname.lower(), "service": SERVICE,
            "message": record.getMessage(), "trace_id": getattr(record, "trace_id", "-"),
        })


logger = logging.getLogger(SERVICE)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.handlers = [handler]


def render_metrics():
    buckets = "".join(
        f'http_request_duration_seconds_bucket{{service="{SERVICE}",le="{le if le != float("inf") else "+Inf"}"}} {count}\n'
        for le, count in DURATION_BUCKETS.items()
    )
    return (
        "# TYPE http_requests_total counter\n"
        f'http_requests_total{{service="{SERVICE}"}} {REQUESTS}\n'
        "# TYPE http_request_errors_total counter\n"
        f'http_request_errors_total{{service="{SERVICE}"}} {ERRORS}\n'
        "# TYPE http_request_duration_seconds_sum counter\n"
        f'http_request_duration_seconds_sum{{service="{SERVICE}"}} {REQUEST_SECONDS:.6f}\n'
        + buckets
        + f'http_request_duration_seconds_count{{service="{SERVICE}"}} {REQUESTS}\n'
    )


def fetch(url, trace_id):
    request = urllib.request.Request(url, headers={"X-Trace-ID": trace_id})
    with urllib.request.urlopen(request, timeout=2) as response:
        return json.loads(response.read())


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        global REQUESTS, ERRORS, REQUEST_SECONDS
        started = time.monotonic()
        trace_id = self.headers.get("X-Trace-ID") or uuid.uuid4().hex
        REQUESTS += 1
        status = 200
        try:
            if self.path == "/healthz":
                payload = {"status": "ok", "service": SERVICE, "trace_id": trace_id}
            elif self.path == "/metrics":
                self._send(render_metrics().encode(), "text/plain; version=0.0.4")
                return
            elif SERVICE == "gateway" and self.path in ("/", "/api/catalog", "/api/orders"):
                payload = {"service": SERVICE, "catalog": fetch(CATALOG_URL + "/api/catalog", trace_id),
                           "orders": fetch(ORDERS_URL + "/api/orders", trace_id), "trace_id": trace_id}
            elif SERVICE == "catalog" and self.path == "/api/catalog":
                payload = {"items": [{"id": 1, "name": "platform-monitor"}], "trace_id": trace_id}
            elif SERVICE == "orders" and self.path == "/api/orders":
                payload = {"orders": [{"id": "order-1", "status": "ready"}], "trace_id": trace_id}
            else:
                status, payload = 404, {"error": "not found", "trace_id": trace_id}
            self._send(json.dumps(payload).encode(), "application/json", status)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            ERRORS += 1
            status = 502
            logger.error("upstream request failed: %s", exc, extra={"trace_id": trace_id})
            self._send(json.dumps({"error": "upstream unavailable", "trace_id": trace_id}).encode(), "application/json", status)
        finally:
            elapsed = time.monotonic() - started
            REQUEST_SECONDS += elapsed
            for bucket in DURATION_BUCKETS:
                if elapsed <= bucket:
                    DURATION_BUCKETS[bucket] += 1
            logger.info("request %s %s", self.path, status, extra={"trace_id": trace_id})

    def _send(self, body, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
