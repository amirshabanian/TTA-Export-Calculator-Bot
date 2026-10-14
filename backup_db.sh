#!/usr/bin/env bash
set -euo pipefail
DB="/var/lib/tta-bot/tta_bot.db"
DEST="/var/lib/tta-bot/backups"
mkdir -p "$DEST"
if [[ ! -f "$DB" ]]; then
  echo "Database not found: $DB" >&2
  exit 1
fi
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
# SQLite online backup API gives a consistent snapshot even if the bot is running.
/usr/bin/python3 - "$DB" "$DEST/tta_bot_$STAMP.db" <<'PY'
import sqlite3, sys
src, dst = sys.argv[1:]
with sqlite3.connect(src, timeout=30) as source, sqlite3.connect(dst) as target:
    source.backup(target)
    result = target.execute('PRAGMA integrity_check').fetchone()[0]
    if result != 'ok':
        raise SystemExit('SQLite integrity_check failed: ' + str(result))
PY
chmod 0640 "$DEST/tta_bot_$STAMP.db"
chown tta-bot:tta-bot "$DEST/tta_bot_$STAMP.db"
find "$DEST" -type f -name 'tta_bot_*.db' -mtime +14 -delete
