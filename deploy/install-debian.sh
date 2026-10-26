#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then echo "Run as root" >&2; exit 1; fi
APP_DIR=/opt/longwave
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

apt-get update
apt-get install -y --no-install-recommends python3 python3-venv ca-certificates
id longwave >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin longwave
mkdir -p "$APP_DIR" /var/cache/longwave
cp -a "$SRC_DIR"/. "$APP_DIR"/
rm -rf "$APP_DIR/.venv"
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --no-cache-dir --upgrade pip
"$APP_DIR/.venv/bin/pip" install --no-cache-dir "$APP_DIR"
chown -R longwave:longwave "$APP_DIR" /var/cache/longwave
install -m 0644 "$APP_DIR/deploy/longwave.service" /etc/systemd/system/longwave.service
systemctl daemon-reload
systemctl enable --now longwave
systemctl --no-pager --full status longwave || true

echo
echo "Longwave is listening only on http://127.0.0.1:8080"
echo "Next: install cloudflared and point your tunnel ingress at that address."
