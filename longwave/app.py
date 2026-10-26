from __future__ import annotations

import os
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request

from .cache import JsonCache
from .core import add_wma, metrics, weekly_close
from .providers import ProviderError, fetch_daily

DEFAULT_START = int(os.getenv("LONGWAVE_START_YEAR", "2015"))
CACHE_TTL = int(os.getenv("LONGWAVE_CACHE_TTL", "21600"))
CACHE_PATH = os.getenv("LONGWAVE_CACHE_PATH", "/var/cache/longwave/series.json")
ALLOWED_SOURCES = {"auto", "coinbase", "binance"}

app = Flask(__name__, static_folder="../static", template_folder="../templates")
app.config.update(MAX_CONTENT_LENGTH=1024, JSON_SORT_KEYS=False)


def build_payload(source: str = "auto") -> dict:
    start = datetime(DEFAULT_START, 1, 1, tzinfo=timezone.utc)
    end = datetime.now(timezone.utc)
    used_source, daily = fetch_daily(start, end, source)
    series = add_wma(weekly_close(daily), 200)
    return {
        "generated_at": end.isoformat(),
        "source": used_source,
        "window_weeks": 200,
        "series": series,
        "metrics": metrics(series),
    }


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
        "base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
    )
    return response


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def healthz():
    return jsonify({"ok": True})


@app.get("/api/series")
def api_series():
    source = request.args.get("source", "auto").lower()
    if source not in ALLOWED_SOURCES:
        return jsonify({"error": "invalid source"}), 400

    cache = JsonCache(CACHE_PATH, CACHE_TTL)
    if source == "auto":
        cached = cache.read()
        if cached:
            return jsonify(cached)

    try:
        payload = build_payload(source)
    except (ProviderError, ValueError) as exc:
        return jsonify({"error": "upstream unavailable", "detail": str(exc)}), 502

    if source == "auto":
        try:
            cache.write(payload)
        except OSError:
            pass
    return jsonify(payload)
