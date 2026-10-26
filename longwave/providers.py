from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USER_AGENT = "longwave/0.1 (+self-hosted market chart)"


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class DailyPoint:
    ts: int
    close: float


def _get_json(url: str, timeout: int = 15):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                raise ProviderError(f"HTTP {r.status} from upstream")
            return json.load(r)
    except Exception as exc:
        raise ProviderError(str(exc)) from exc


def coinbase_daily(start: datetime, end: datetime) -> list[DailyPoint]:
    """Fetch BTC-USD daily candles from Coinbase Exchange public market data."""
    base = "https://api.exchange.coinbase.com/products/BTC-USD/candles"
    cursor = start.astimezone(timezone.utc)
    end = end.astimezone(timezone.utc)
    out: dict[int, DailyPoint] = {}

    while cursor < end:
        chunk_end = min(cursor + timedelta(days=290), end)
        qs = urlencode({
            "granularity": 86400,
            "start": cursor.isoformat().replace("+00:00", "Z"),
            "end": chunk_end.isoformat().replace("+00:00", "Z"),
        })
        rows = _get_json(f"{base}?{qs}")
        if not isinstance(rows, list):
            raise ProviderError("Unexpected Coinbase response")
        for row in rows:
            if isinstance(row, list) and len(row) >= 5:
                ts, close = int(row[0]), float(row[4])
                out[ts] = DailyPoint(ts, close)
        cursor = chunk_end
        time.sleep(0.08)

    points = sorted(out.values(), key=lambda p: p.ts)
    if not points:
        raise ProviderError("Coinbase returned no price data")
    return points


def binance_daily(start: datetime, end: datetime) -> list[DailyPoint]:
    """Fallback public BTCUSDT daily candles from Binance."""
    base = "https://api.binance.com/api/v3/klines"
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    out: list[DailyPoint] = []

    while start_ms < end_ms:
        qs = urlencode({
            "symbol": "BTCUSDT",
            "interval": "1d",
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 1000,
        })
        rows = _get_json(f"{base}?{qs}")
        if not isinstance(rows, list):
            raise ProviderError("Unexpected Binance response")
        if not rows:
            break
        for row in rows:
            ts = int(row[0] // 1000)
            out.append(DailyPoint(ts, float(row[4])))
        next_ms = int(rows[-1][0]) + 86_400_000
        if next_ms <= start_ms:
            break
        start_ms = next_ms
        time.sleep(0.08)

    if not out:
        raise ProviderError("Binance returned no price data")
    return out


def fetch_daily(start: datetime, end: datetime, source: str = "auto") -> tuple[str, list[DailyPoint]]:
    source = source.lower()
    if source == "coinbase":
        return "coinbase", coinbase_daily(start, end)
    if source == "binance":
        return "binance", binance_daily(start, end)
    if source != "auto":
        raise ValueError("source must be auto, coinbase, or binance")

    errors: list[str] = []
    for name, fn in (("coinbase", coinbase_daily), ("binance", binance_daily)):
        try:
            return name, fn(start, end)
        except ProviderError as exc:
            errors.append(f"{name}: {exc}")
    raise ProviderError("; ".join(errors))
