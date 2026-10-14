#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/tta-bot"
DATA_DIR="/var/lib/tta-bot"
SERVICE_USER="tta-bot"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run with sudo: sudo bash scripts/install_ubuntu.sh"
  exit 1
fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip python3-dev build-essential ca-certificates tzdata unzip

if ! id -u "$SERVICE_USER" >/dev/null 2>&1; then
  useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
fi
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0750 "$APP_DIR" "$DATA_DIR" "$DATA_DIR/backups"

# This script expects the ZIP to have already been extracted to a working directory.
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
install -m 0640 "$SRC_DIR/bot.py" "$APP_DIR/bot.py"
install -m 0640 "$SRC_DIR/requirements.txt" "$APP_DIR/requirements.txt"
install -m 0640 "$SRC_DIR/test_calculations.py" "$APP_DIR/test_calculations.py"
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0750 "$APP_DIR/scripts"
install -m 0750 "$SRC_DIR/scripts/backup_db.sh" "$APP_DIR/scripts/backup_db.sh"
chown "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"/*.py "$APP_DIR/requirements.txt"

python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/python" -m pip install --upgrade pip wheel
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

if [[ ! -f "$APP_DIR/.env" ]]; then
  install -o root -g "$SERVICE_USER" -m 0640 "$SRC_DIR/.env.example" "$APP_DIR/.env"
  echo
  echo "IMPORTANT: Edit $APP_DIR/.env and replace TELEGRAM_BOT_TOKEN before starting the service."
fi

install -m 0644 "$SRC_DIR/tta-bot.service" /etc/systemd/system/tta-bot.service
systemctl daemon-reload

echo
"$APP_DIR/.venv/bin/python" -m py_compile "$APP_DIR/bot.py"
(cd "$APP_DIR" && "$APP_DIR/.venv/bin/python" -m unittest test_calculations) || {
  echo "Tests failed. Service has NOT been enabled or started." >&2
  exit 2
}

echo "Install completed. Configure $APP_DIR/.env, then run:"
echo "  sudo systemctl enable --now tta-bot"
echo "  sudo journalctl -u tta-bot -f"
