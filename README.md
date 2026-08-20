# 🇮🇷🇬🇧 T.T.A Export Calculator

A bilingual Persian/English Telegram bot for calculating export landed cost per kilogram.

## Features

- Works with any product: dates, apples, kiwi, figs, raisins, etc.
- User-defined packaging: carton, basket, box, pallet, etc.
- Variable number of packages.
- Variable **gross weight per package**.
- Product price per KG.
- Packaging & labor cost per KG.
- Product profit margin per KG.
- Inland freight to Bandar Abbas.
- Customs clearance cost.
- Sea freight in USD.
- USD exchange rate.
- Destination.
- Automatic landed-cost calculation.
- Automatic customer-price calculation.
- Bilingual Persian/English interface.
- Formula explanation inside the bot.

## Important calculation basis

This version intentionally uses **GROSS WEIGHT** as the calculation basis.

Total Gross Weight:

`Number of Packages × Gross Weight per Package`

Origin Product Price:

`Product Price + Packaging & Labor + Product Profit`

Landed Cost:

`(Product Cost + Inland Freight + Customs Clearance + Sea Freight × USD Rate) / Total Gross Weight / USD Rate`

Customer Price:

The landed cost is rounded **UP** to the next $0.05 so the quoted price is never below calculated cost.

## Requirements

- Python 3.10+
- Telegram Bot Token
- A hosting service such as Railway, Render, Fly.io, VPS, etc.

## Railway deployment

1. Create a GitHub repository and upload:
   - `bot.py`
   - `requirements.txt`
   - `.gitignore`
   - `README.md`

2. Create a Railway project.
3. Connect the GitHub repository.
4. Add this environment variable:

`TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN`

Never put the token inside `bot.py` or commit it to GitHub.

5. Deploy.

Railway will install the packages from `requirements.txt` and run the bot.

If Railway does not automatically detect the start command, use:

`python bot.py`

## Updating

Replace `bot.py` and commit the change to GitHub.

If Railway is connected with automatic deployments enabled, it will redeploy automatically.

Otherwise open Railway:

`Deployments → Redeploy`

## Security

Do not publish a Telegram bot token.

If a token is accidentally exposed, revoke it in BotFather and create a new token.

## License

You may adapt this project for your own export-cost calculations.


## Customer quotation output

After a calculation, the operator can press `📄 خروجی مشتری | Customer Quotation`. The bot sends a customer-safe Telegram message and a PDF quotation. The customer copy contains only product, packaging, packages, gross weight, destination, final USD/KG offer and total shipment value. Internal product price, packaging/labor, profit, inland freight, customs, sea freight, exchange rate and landed cost are never included.

### Update
Replace `bot.py` and `requirements.txt` in GitHub and commit. Railway will redeploy automatically if Auto Deploy is enabled. Keep `TELEGRAM_BOT_TOKEN` only in Railway Variables; never upload the token to GitHub.


## v5.0.0 - Customer quotation improvements

- Customer name is now requested before generating the quotation.
- Customer-facing PDF is English-only to avoid missing Persian-font squares.
- Added T.T.A company information and Bandar Abbas address.
- Added company mobile number in international format.
- Added company logo file (`tta_logo.png`).
- Customer-facing output continues to hide all internal purchase costs, operating costs and profit margin.
