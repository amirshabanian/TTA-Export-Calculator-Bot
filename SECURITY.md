# Security Policy

- Never commit `.env`, Telegram bot tokens, private keys, database files, logs, or customer documents.
- Configure secrets in Railway Variables or a private VPS `.env` file.
- If a token is exposed, revoke it with Telegram BotFather immediately and update the host.
- Restrict VPS file permissions and access to backups.
- Use one long-polling instance per bot token.
- Do not post production logs publicly without redacting IDs and personal/customer data.
- Report security issues privately to the maintainer rather than opening a public issue containing secrets.

