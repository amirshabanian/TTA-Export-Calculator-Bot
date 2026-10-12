# Deployment checklist — T.T.A Export Calculator

## Before uploading
- [ ] Confirm `bot.py` is the latest tested version.
- [ ] Ensure no Telegram bot token, API secret, private key, or `.env` file is in the repository.
- [ ] Review dependencies and pin versions after confirming the working environment.
- [ ] Test a full shipment calculation.
- [ ] Generate a customer PDF and verify internal costs are not disclosed.

## GitHub
1. Open `amirshabanian/TTA-Export-Calculator-Bot`.
2. Review the existing `README.md` and `requirements.txt` before replacing them.
3. Do not upload `.env`, SQLite database files, logs, or customer documents.
4. Suggested commit message: `docs: polish project README and deployment guidance`.

## Railway
- Configure `TTA_ADMIN_IDS=5044844036` if this is still the intended administrator ID.
- Set creator contact variables only if the current bot code reads them: `TTA_CREATOR_NAME`, `TTA_CREATOR_PHONE`, `TTA_CREATOR_WHATSAPP`, `TTA_CREATOR_TELEGRAM`.
- Attach a persistent volume and configure SQLite to use its mount path.
- Ensure only one service/replica runs long polling for the bot token.
- Redeploy and inspect logs.

## Important
This package contains documentation and deployment guidance only. It does **not** include a verified replacement for `bot.py` and does not claim that v6.0.4 functional fixes are implemented. Do not overwrite working bot code with an untested file.
