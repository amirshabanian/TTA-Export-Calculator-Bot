# TTA Export Calculator v6.0.0

Professional bilingual Telegram export-cost calculator with:
- 7-day one-time trial per Telegram account
- Per-user license keys bound to Telegram User ID
- Professional user menu
- Admin dashboard for license generation and user/license overview
- Existing export-cost calculation, Tehran/UAE sea-freight payment logic, Switch Bill, Cross Stuffing, company profiles and customer quotation PDF

## Railway Variables

Required:
- `TELEGRAM_BOT_TOKEN`
- `TTA_ADMIN_IDS` — comma-separated Telegram User IDs allowed to use the admin panel

Recommended:
- `TTA_DB_PATH=/data/tta_bot.db` when a persistent Railway Volume is mounted at `/data`
- `TTA_TRIAL_DAYS=7`
- `TTA_CREATOR_NAME`
- `TTA_CREATOR_PHONE`
- `TTA_CREATOR_WHATSAPP`
- `TTA_CREATOR_TELEGRAM`

Never put Telegram tokens or secrets in GitHub.

## How licensing works

1. A new Telegram user gets one automatic 7-day trial.
2. The trial is tied to Telegram User ID and cannot be restarted by reinstalling the bot.
3. Admin creates a 30-day, 90-day, 365-day, or permanent license from the Admin Panel.
4. The bot generates a unique key such as `TTA-ABCD-EFGH-IJKL`.
5. The first account that activates an unused key owns it; later users cannot reuse it.
6. Expired/suspended access cannot start a calculation.

## Deployment

Railway start command:
`python bot.py`

The SQLite database should be placed on a persistent volume for production use.
