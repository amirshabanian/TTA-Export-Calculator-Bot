# 🇮🇷🇬🇧 TTA Export Calculator v5.2.0

A bilingual Persian/English Telegram bot for export landed-cost calculation and customer-safe quotation generation.

## What is new in v5.2.0?

### 👤 Multi-user company profiles
Each Telegram user can save their own:

- Company name
- Company address
- Company phone / WhatsApp
- Company logo

The customer quotation uses the profile of the **user who created the quotation**. TTA company details are no longer hard-coded for every user.

Use:

`/profile`

or the **🏢 Company Profile** button.

The profile is stored by Telegram User ID in SQLite.

### 🚢 Optional logistics costs
Two optional USD costs were added:

- Switch Bill of Lading
- Cross Stuffing

If a cost is not applicable, enter `0`.

These costs are included in the internal landed-cost calculation but are **never shown to the customer**.

## Current calculation inputs

1. Product
2. Packaging type
3. Number of packages
4. Gross weight per package
5. Product price / KG
6. Packaging & labor / KG
7. Product profit margin / KG
8. Inland freight to Bandar Abbas
9. Customs clearance
10. Sea freight / USD
11. Switch Bill / USD (optional)
12. Cross Stuffing / USD (optional)
13. USD exchange rate
14. Destination
15. Customer name

## Calculation basis

The bot uses **GROSS WEIGHT** as the commercial calculation basis.

### Total Gross Weight

`Packages × Gross Weight per Package`

### Origin Product Price

`Product Price + Packaging & Labor + Product Profit`

### Export Freight in USD

`Sea Freight + Switch Bill + Cross Stuffing`

### Landed Cost

`(Product Cost + Inland Freight + Customs + Export Freight × USD Rate) ÷ Total Gross Weight ÷ USD Rate`

### Customer Price

The landed cost is rounded **UP** to the next `$0.05` so the automatic customer price does not fall below the calculated cost.

## Customer quotation

The customer-facing message and PDF contain only commercial information such as:

- Customer name
- Product
- Packaging
- Number of packages
- Gross weight
- Destination
- Final offer price / KG
- Total shipment value
- The current user's company name, address, phone and logo

The following are intentionally hidden:

- Product purchase price
- Packaging & labor cost
- Internal profit margin
- Inland freight
- Customs clearance
- Sea freight
- Switch Bill cost
- Cross Stuffing cost
- USD exchange rate
- Internal landed cost

The customer quotation is English-only to avoid Persian font-rendering problems in PDF output.

## Requirements

- Python 3.10+
- Telegram Bot Token
- `python-telegram-bot==22.5`
- ReportLab
- Pillow

## Railway deployment

1. Connect this GitHub repository to Railway.
2. Add the environment variable:

`TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN`

Never put the token in GitHub.

3. Start command:

`python bot.py`

### Database / profiles

The bot creates `tta_bot.db` automatically.

For production use with multiple users, a persistent Railway Volume is recommended and `TTA_DB_PATH` can be set to a path on that volume, for example:

`TTA_DB_PATH=/data/tta_bot.db`

Without persistent storage, company profiles may be lost when the hosting service replaces the container during a new deployment.

## Updating

Replace the project files in GitHub and commit the update.

Recommended release tag:

`v5.2.0`

If Railway Auto Deploy is enabled, a new GitHub commit should trigger a new deployment. Otherwise use Railway's Redeploy option.

## Security

Never publish a Telegram bot token.

If a token is exposed, revoke it in BotFather and create a new token, then update the Railway variable.

## License

You may adapt this project for your own export-cost calculations.

## Version history

### v5.2.0
- Multi-user company profiles
- Per-user company name, address and phone
- Per-user Telegram logo file ID
- Customer quotation uses the current user's company details
- Optional Switch Bill of Lading cost
- Optional Cross Stuffing cost
- New costs included in landed-cost calculation
- New costs hidden from customer quotation
- SQLite profile storage
- Railway persistent-storage guidance

### v5.1.0
- Official TTA company logo
- Customer quotation improvements
- English-only customer PDF
- Customer name field
- Gross-weight calculation basis
