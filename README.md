# Longwave

A tiny self-hosted web view of BTC/USD weekly price versus its 200-week moving average.

The repository name is intentionally generic; the application is read-only and performs no wallet, node, trading, or account operations.

## Features

- Coinbase public market data by default
- Binance public market data as automatic fallback
- 200-week moving average computed from weekly closes
- logarithmic chart rendered in vanilla JavaScript
- below-baseline shading
- price / baseline / distance summary
- 6-hour disk cache by default
- `/healthz` endpoint
- Gunicorn + hardened systemd unit
- designed for `127.0.0.1` behind Cloudflare Tunnel

## Quick start (Debian 12/13 LXC)

```bash
apt update && apt install -y git
cd /opt
git clone https://github.com/bitemybits/longwave.git
cd longwave
sudo ./deploy/install-debian.sh
curl http://127.0.0.1:8080/healthz
```

The service does not need a public listening port when `cloudflared` runs in the same LXC.

## Cloudflare Tunnel

Route your hostname to:

```text
http://127.0.0.1:8080
```

Example:

```yaml
tunnel: YOUR_TUNNEL_UUID
credentials-file: /etc/cloudflared/YOUR_TUNNEL_UUID.json

ingress:
  - hostname: chart.example.com
    service: http://127.0.0.1:8080
  - service: http_status:404
```

## Local development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
flask --app longwave.app run --host 127.0.0.1 --port 8080
```

Tests:

```bash
pytest -q
```

## API

```text
GET /api/series
GET /api/series?source=coinbase
GET /api/series?source=binance
GET /healthz
```

## Configuration

| Variable | Default | Purpose |
|---|---:|---|
| `LONGWAVE_START_YEAR` | `2015` | first year requested from the provider |
| `LONGWAVE_CACHE_TTL` | `21600` | cache lifetime in seconds |
| `LONGWAVE_CACHE_PATH` | `/var/cache/longwave/series.json` | cache file |

## Security

- Gunicorn binds to `127.0.0.1:8080`.
- No login, uploads, forms, shell execution, wallet integration, trading endpoints, or write API.
- Defensive HTTP headers are applied.
- The systemd unit enables filesystem and kernel protections.
- Cloudflare Access can be added if you want the chart private.

## Limitations

- Public exchange APIs can throttle or temporarily fail.
- Coinbase history for this market does not cover the earliest Bitcoin years.
- Binance uses `BTCUSDT` as a USD proxy.
- The 200-week line is a simple average of weekly closes.

## License

MIT
