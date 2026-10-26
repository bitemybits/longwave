from datetime import datetime, timezone, timedelta
from longwave.core import add_wma, metrics, weekly_close
from longwave.providers import DailyPoint


def test_weekly_close_keeps_last_point_of_week():
    base = datetime(2025, 1, 6, tzinfo=timezone.utc)
    pts = [DailyPoint(int((base + timedelta(days=i)).timestamp()), 100+i) for i in range(8)]
    rows = weekly_close(pts)
    assert len(rows) == 2
    assert rows[0]["price"] == 106
    assert rows[1]["price"] == 107


def test_moving_average_and_metrics():
    rows = [{"date": f"d{i}", "ts": i, "price": float(i+1)} for i in range(4)]
    got = add_wma(rows, window=3)
    assert got[1]["wma"] is None
    assert got[2]["wma"] == 2.0
    assert got[3]["wma"] == 3.0
    m = metrics(got)
    assert m["price"] == 4.0
    assert m["wma"] == 3.0
    assert m["distance_pct"] == 33.33
