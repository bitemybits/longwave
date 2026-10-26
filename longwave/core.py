from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from .providers import DailyPoint


def weekly_close(points: list[DailyPoint]) -> list[dict]:
    weeks: "OrderedDict[tuple[int, int], DailyPoint]" = OrderedDict()
    for p in sorted(points, key=lambda x: x.ts):
        dt = datetime.fromtimestamp(p.ts, timezone.utc)
        iso = dt.isocalendar()
        weeks[(iso.year, iso.week)] = p
    return [
        {
            "ts": p.ts,
            "date": datetime.fromtimestamp(p.ts, timezone.utc).date().isoformat(),
            "price": round(p.close, 2),
        }
        for p in weeks.values()
    ]


def add_wma(rows: list[dict], window: int = 200) -> list[dict]:
    prices: list[float] = []
    total = 0.0
    result: list[dict] = []
    for row in rows:
        price = float(row["price"])
        prices.append(price)
        total += price
        if len(prices) > window:
            total -= prices[-window - 1]
        wma = round(total / window, 2) if len(prices) >= window else None
        result.append({**row, "wma": wma, "below": bool(wma is not None and price < wma)})
    return result


def metrics(rows: list[dict]) -> dict:
    valid = [r for r in rows if r.get("wma") is not None]
    if not valid:
        return {"price": None, "wma": None, "distance_pct": None, "weeks_below": 0}
    latest = valid[-1]
    distance = (latest["price"] / latest["wma"] - 1.0) * 100.0
    return {
        "price": latest["price"],
        "wma": latest["wma"],
        "distance_pct": round(distance, 2),
        "weeks_below": sum(1 for r in valid if r["below"]),
    }
