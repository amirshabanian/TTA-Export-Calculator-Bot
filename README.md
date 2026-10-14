<div align="center">

# 🌿 T.T.A Export Cost Calculator Bot

**Telegram bot for export landed-cost calculations and customer-ready quotation PDFs**

[English](README.md) · [فارسی](README.fa.md) · [简体中文](README.zh-CN.md) · [Русский](README.ru.md) · [Türkçe](README.tr.md)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4)
![Storage](https://img.shields.io/badge/Storage-SQLite-003B57)
![Status](https://img.shields.io/badge/Release-6.2.0--ORACLE-orange)

</div>

T.T.A Export Cost Calculator helps exporters estimate shipment costs and prepare customer-facing quotation PDFs. It is maintained by **Amir Shabanian**, Founder of **Shabanian Trading** and Business Partner at **Tamana Tejarat Armaghan (T.T.A)**.

> **Important:** The language links above open separately maintained README files. GitHub does not automatically translate a README when a visitor changes GitHub's interface language.

## Features

- Persian/English Telegram workflow (depending on the bot flow)
- Product, packaging, gross/net weight and quantity inputs
- Inland transport, customs, packing/labor and sea-freight cost inputs
- Freight-payment options and exchange-rate inputs
- Landed-cost calculation and customer quotation generation
- Customer-facing PDF quotation designed to avoid disclosing internal cost details
- SQLite-backed user/license state
- Admin panel, trial and license workflow
- Ubuntu systemd service template and database backup helper

## Project contents

- `bot.py` — Telegram bot application
- `requirements.txt` — Python dependencies
- `.env.example` — environment-variable template; never put real secrets here
- `tta-bot.service` — systemd unit for a Linux VPS
- `scripts/install_ubuntu.sh` — VPS installation helper
- `scripts/backup_db.sh` — SQLite backup helper
- `test_calculations.py` — calculation tests
- `README.fa.md` — Persian guide
- `DEPLOYMENT.md` — Railway and VPS deployment/update instructions
- `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md` — project maintenance guidance

## Quick start: local / VPS

Requirements: Python 3.10+ and a Telegram bot token from [BotFather](https://t.me/BotFather).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env locally; never commit it.
python bot.py
```

Set at minimum:
- `TELEGRAM_BOT_TOKEN` — private bot token
- `TTA_ADMIN_IDS` — comma-separated Telegram numeric user IDs
- `TTA_DB_PATH` — database path on persistent storage

See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup, Railway persistent storage, systemd installation, and safe updates.

## Railway deployment

Use one Railway service with a single polling replica. Add variables through Railway's Variables UI, not in source code. If using SQLite, attach a persistent Volume and set `TTA_DB_PATH` to a file inside its mount path. Without persistent storage, user/license data can be lost when the container is replaced. Do not run Railway and VPS polling simultaneously with the same token.

## Security and data

- Never commit `.env`, Telegram tokens, SQLite databases, logs, customer quotations, or private keys.
- Run only one long-polling instance per bot token.
- Back up the SQLite database before updates.
- Review PDF output before sending it to customers.
- See [SECURITY.md](SECURITY.md).

## Tests

```bash
python -m unittest -v
```

The packaged calculation tests cover core calculations only; they do not prove that a live Telegram deployment, Railway networking, or every conversation flow works. Test the bot in Telegram after each deployment.

## Support

- Telegram: [@tamana_tejarat](https://t.me/tamana_tejarat)
- WhatsApp: [Contact](https://wa.me/qr/DDNAEFASNGBAP1)

## Maintainer

**Amir Shabanian**  
Founder of Shabanian Trading · Business Partner at Tamana Tejarat Armaghan (T.T.A)

## License

No license is granted by this repository unless a `LICENSE` file is added. If you intend to publish this as open source, choose and add an appropriate license after confirming ownership and redistribution rights for all code and assets.
