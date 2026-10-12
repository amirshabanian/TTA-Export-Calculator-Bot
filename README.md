# T.T.A Export Cost Calculator Bot

**A bilingual Telegram assistant for export cost estimation and customer-ready quotations.**

Developed by **Amir Shabanian**  
Founder of Shabanian Trading | Business Partner at Tamana Tejarat Armaghan (T.T.A)

## Overview

T.T.A Export Cost Calculator helps exporters estimate shipment costs and prepare a clean, English-language quotation PDF for customers. It is built with Python, `python-telegram-bot`, SQLite, and ReportLab.

## Core workflow

1. Enter product and packaging details.
2. Enter package count, gross/net weight, and product cost.
3. Add packing/labor, inland transport, customs, and sea freight.
4. Select freight payment method and enter applicable exchange rates.
5. Calculate landed cost and a customer quote rounded upward to the next USD 0.05.
6. Generate a customer-facing PDF that excludes internal cost breakdowns.

## Features

- Persian and English prompts
- Shipment cost calculations
- Tehran freight payment with configurable tax
- UAE freight payment in AED with configurable USD/AED rate
- Optional switch-bill and cross-stuffing charges
- Customer quotation PDF
- SQLite-backed user/license data
- Admin tools and trial/license workflow (depending on deployed bot version)

## Deployment notes

- Store the Telegram bot token only in hosting environment variables. Never commit it to GitHub.
- Run only **one polling instance** for a bot token. Multiple instances can trigger `Conflict: terminated by other getUpdates request`.
- Configure a persistent Railway Volume for SQLite; temporary container storage may be lost during redeployment.
- Verify admin configuration and test a full calculation and PDF after deployment.

## Contact the developer

**Amir Shabanian**  
Founder of Shabanian Trading | Business Partner at Tamana Tejarat Armaghan (T.T.A)

- WhatsApp: [Contact on WhatsApp](https://wa.me/qr/DDNAEFASNGBAP1)
- Telegram: [@tamana_tejarat](https://t.me/tamana_tejarat)
- TON wallet (optional project support): `UQDRwAh-L8KRqTIxoDBTmBs-oc0qwF3fTIqVN0oqJpSLjdCZ`

Thank you for using and supporting this project.
