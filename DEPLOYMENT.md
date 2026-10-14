# Deployment and Update Guide

This guide covers the packaged T.T.A Export Cost Calculator Bot (`bot.py`) on Railway and Ubuntu VPS.

## 0. Before you start

- Create a backup of the current SQLite database.
- Keep the Telegram token private.
- Run **only one polling instance** per bot token. Stop the old host before starting the new one.
- Do not replace a production database with a fresh empty database.
- Confirm the uploaded `bot.py` is the version you intend to deploy.

## 1. Environment variables

Set these in the host's secret/environment-variable UI or in a private `.env` file on the VPS:

```dotenv
TELEGRAM_BOT_TOKEN=YOUR_REAL_TOKEN
TTA_ADMIN_IDS=5044844036
TTA_DB_PATH=/var/lib/tta-bot/tta_bot.db
TTA_TRIAL_DAYS=7
TTA_CREATOR_NAME=Amir Shabanian
TTA_CREATOR_PHONE=+98 939 625 5418
TTA_CREATOR_WHATSAPP=https://wa.me/qr/DDNAEFASNGBAP1
TTA_CREATOR_TELEGRAM=https://t.me/tamana_tejarat
```

Use the exact variables supported by the checked-in `bot.py`. Never paste a real token into GitHub, an issue, a screenshot, or a chat. If a token is exposed, revoke it with BotFather and replace it on the host.

## 2. Railway deployment

1. Upload the project files to a GitHub repository.
2. In Railway, create/select a project and deploy from the repository.
3. Set the environment variables in **Variables**. Do not create a committed `.env`.
4. Configure the start command as `python bot.py` if Railway does not detect it automatically.
5. For SQLite, attach a **persistent Volume**. Set `TTA_DB_PATH` to a database file inside that Volume's mount path. Confirm the mount path in Railway's current UI; do not assume it is `/data` unless that is the configured mount path.
6. Set the service to one replica/instance when using long polling.
7. Deploy, inspect logs, then test `/start`, `/admin`, one complete calculation, and PDF generation.
8. If migrating from a running VPS, stop the VPS service before starting Railway. Reverse this order when migrating back.

**Data warning:** Railway's ephemeral filesystem can be replaced during deploy/restart. SQLite data must live on a persistent mounted volume. Back up the database before changing mount paths.

## 3. Ubuntu VPS: fresh install

Recommended for Ubuntu 22.04+ and Python 3.10+.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential
sudo mkdir -p /opt/tta-bot /var/lib/tta-bot
sudo chown -R "$USER":"$USER" /opt/tta-bot
```

Copy the project files into `/opt/tta-bot`, then:

```bash
cd /opt/tta-bot
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
nano .env
```

Create a dedicated service account and protect files (skip account creation if it already exists):

```bash
sudo useradd --system --home /opt/tta-bot --shell /usr/sbin/nologin tta-bot 2>/dev/null || true
sudo chown -R tta-bot:tta-bot /opt/tta-bot /var/lib/tta-bot
sudo chmod 640 /opt/tta-bot/.env
```

Review `tta-bot.service`. It assumes `/opt/tta-bot/.venv/bin/python`, `/opt/tta-bot/bot.py`, and `/var/lib/tta-bot` for writable database storage. Then:

```bash
sudo cp tta-bot.service /etc/systemd/system/tta-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now tta-bot
sudo systemctl status tta-bot --no-pager
sudo journalctl -u tta-bot -n 100 --no-pager
```

If your service account or file ownership differs, correct it before starting. Do not change firewall or 3X-UI settings for a polling bot; it normally makes outbound HTTPS requests.

## 4. Updating an existing VPS safely

**Do not blindly overwrite the database or `.env`.** Run commands one by one and verify paths.

1. Stop the service:
   ```bash
   sudo systemctl stop tta-bot
   ```
2. Back up the database (adjust path if your configured `TTA_DB_PATH` differs):
   ```bash
   sudo install -d -m 750 /var/backups/tta-bot
   sudo cp -a /var/lib/tta-bot/tta_bot.db "/var/backups/tta-bot/tta_bot.db.$(date +%Y%m%d-%H%M%S)"
   ```
3. Back up current code and configuration:
   ```bash
   sudo tar -czf "/var/backups/tta-bot/code-$(date +%Y%m%d-%H%M%S).tar.gz" /opt/tta-bot --exclude=/opt/tta-bot/.venv
   ```
   Keep the `.env` backup private; never upload it.
4. Upload the new project files, preserving `.env` and the existing SQLite database.
5. Install updated dependencies:
   ```bash
   cd /opt/tta-bot
   sudo -u tta-bot /opt/tta-bot/.venv/bin/pip install -r requirements.txt
   ```
6. Run the available tests:
   ```bash
   cd /opt/tta-bot
   sudo -u tta-bot /opt/tta-bot/.venv/bin/python -m unittest -v
   ```
7. Start and inspect:
   ```bash
   sudo systemctl start tta-bot
   sudo systemctl status tta-bot --no-pager
   sudo journalctl -u tta-bot -n 100 --no-pager
   ```
8. Test Telegram `/start`, `/admin`, calculation, and PDF output. If it fails, stop service and inspect logs before rollback.

**Rollback:** stop the service, restore the previous `bot.py` and dependency set from your backup, then start the service. Restore the database only if it was modified and you understand the data-loss implications.

## 5. Migration between Railway and VPS

1. Decide which host will be authoritative.
2. Stop polling on the old host.
3. Back up the old SQLite database using a supported download/backup method.
4. Transfer the database securely to the new host and set `TTA_DB_PATH` to that file.
5. Verify file permissions and that the bot user can write to the database directory.
6. Start the new host and test admin access, user/license records, calculation, and PDF.
7. Keep a private backup until the new deployment is verified.

Never run two active polling instances with the same bot token. This can cause Telegram `Conflict: terminated by other getUpdates request` errors.

## 6. Troubleshooting

- `Conflict: terminated by other getUpdates request`: another instance is polling with the same token; stop the duplicate.
- Service exits immediately: check `journalctl -u tta-bot -n 100 --no-pager`, environment variables, dependency installation and file permissions.
- Admin panel missing: verify `TTA_ADMIN_IDS` contains the correct numeric Telegram user ID, with no `@` symbol, then restart the service.
- User/license data missing: verify `TTA_DB_PATH` and confirm the database file was migrated; do not create a fresh DB over the old one.
- PDF failure: check ReportLab/Pillow dependencies and logs.

## 7. Pre-release checklist

- [ ] No `.env`, tokens, databases, logs, customer files, or private keys are committed.
- [ ] One polling instance only.
- [ ] Persistent database storage configured.
- [ ] Backup completed.
- [ ] Unit tests pass.
- [ ] `/start` and `/admin` work.
- [ ] A full calculation and PDF generation are verified.
- [ ] Update and rollback steps have been tested.
