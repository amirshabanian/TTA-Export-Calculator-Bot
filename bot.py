import os
import logging
from decimal import Decimal, InvalidOperation, ROUND_UP
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)

# ============================================================
# T.T.A EXPORT CALCULATOR
# Public / bilingual Telegram bot
#
# Environment variable required:
#   TELEGRAM_BOT_TOKEN
#
# IMPORTANT:
# Never put your Telegram bot token inside this file or GitHub.
# Add it as an environment variable on Railway/Render/etc.
# ============================================================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("tta-export-calculator")

(
    PRODUCT, PACKAGING, PACKAGES, GROSS_KG,
    PRODUCT_PRICE, PACK_LABOR, PROFIT,
    LAND, CLEARANCE, SEA, FX, DESTINATION
) = range(12)
CUSTOMER = 12


def to_decimal(value: str) -> Decimal:
    """Convert user-entered number to Decimal."""
    try:
        cleaned = str(value).replace(",", "").replace("٬", "").replace("٫", ".").strip()
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        raise ValueError("Invalid number")


def money(value: Decimal, decimals: int = 0) -> str:
    return f"{value:,.{decimals}f}"


def calculate(data):
    """
    Main calculation.

    IMPORTANT:
    This version intentionally uses GROSS WEIGHT as the commercial
    calculation basis, as requested by T.T.A.

    Product price per KG =
        product price + packaging/labor + product profit

    Total product cost =
        total gross KG * product price per KG

    Export costs =
        inland freight + customs clearance + sea freight converted
        to local currency

    Landed cost per KG in USD =
        (product cost + export costs) / gross KG / USD rate

    Customer price =
        landed cost rounded UP to the next 0.05 USD.
    """
    packages = to_decimal(data["packages"])
    gross_per_package = to_decimal(data["gross_kg"])
    product_price = to_decimal(data["product_price"])
    pack_labor = to_decimal(data["pack_labor"])
    profit = to_decimal(data["profit"])
    land = to_decimal(data["land"])
    clearance = to_decimal(data["clearance"])
    sea_usd = to_decimal(data["sea_usd"])
    fx = to_decimal(data["fx"])

    total_gross = packages * gross_per_package
    origin_price_kg = product_price + pack_labor + profit
    product_total = total_gross * origin_price_kg

    sea_local = sea_usd * fx
    export_total = land + clearance + sea_local
    total_cost = product_total + export_total

    cost_local_kg = total_cost / total_gross
    cost_usd_kg = cost_local_kg / fx

    # Automatic customer price:
    # round UP to the next 0.05 USD, so the quote never falls below cost.
    step = Decimal("0.05")
    customer_price = (cost_usd_kg / step).to_integral_value(rounding=ROUND_UP) * step

    return {
        "total_gross": total_gross,
        "origin_price_kg": origin_price_kg,
        "product_total": product_total,
        "sea_local": sea_local,
        "export_total": export_total,
        "total_cost": total_cost,
        "cost_local_kg": cost_local_kg,
        "cost_usd_kg": cost_usd_kg,
        "customer_price": customer_price,
        "shipment_value": customer_price * total_gross,
    }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton("🧮 محاسبه جدید | New Calculation", callback_data="new")],
        [InlineKeyboardButton("ℹ️ راهنما | Help", callback_data="help")],
    ]

    await update.message.reply_text(
        "🇮🇷 T.T.A Export Calculator 🇬🇧\n\n"
        "محاسبه قیمت تمام‌شده صادرات برای محصولات مختلف.\n"
        "Export landed-cost calculator for different products.\n\n"
        "خرما | Dates • سیب | Apples • کیوی | Kiwi • انجیر | Figs • "
        "کشمش | Raisins • ...",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def begin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        message = update.callback_query.message
    else:
        message = update.message

    context.user_data.clear()

    await message.reply_text(
        "نام محصول را وارد کنید.\n"
        "Enter product name.\n\n"
        "مثال | Example: خرما | Dates"
    )
    return PRODUCT


async def text_field(update, context, key, prompt, next_state):
    value = update.message.text.strip()
    if not value:
        await update.message.reply_text("لطفاً مقدار را وارد کنید.")
        return next_state - 1

    context.user_data[key] = value
    await update.message.reply_text(prompt)
    return next_state


async def numeric_field(update, context, key, prompt, current_state):
    try:
        to_decimal(update.message.text)
    except ValueError:
        await update.message.reply_text(
            "❌ عدد نامعتبر است.\n"
            "Please enter a valid number.\n\n"
            "مثال | Example: 3500 or 7.15"
        )
        return current_state

    context.user_data[key] = update.message.text.strip()
    await update.message.reply_text(prompt)
    return current_state + 1


async def product(update, context):
    return await text_field(
        update, context, "product",
        "نوع بسته‌بندی را وارد کنید.\n"
        "Enter packaging type.\n\n"
        "مثال | Example: کارتن | Carton",
        PACKAGING
    )


async def packaging(update, context):
    return await text_field(
        update, context, "packaging",
        "تعداد کل بسته را وارد کنید.\n"
        "Enter total number of packages.\n\n"
        "مثال | Example: 3500",
        PACKAGES
    )


async def packages(update, context):
    return await numeric_field(
        update, context, "packages",
        "وزن ناخالص هر بسته را به کیلو وارد کنید.\n"
        "Enter gross weight per package in KG.\n\n"
        "مثال | Example: 7.15",
        PACKAGES
    )


async def gross(update, context):
    return await numeric_field(
        update, context, "gross_kg",
        "قیمت خود محصول به ازای هر کیلو، به تومان.\n"
        "Product price per KG, in Toman.\n\n"
        "مثال | Example: 133000",
        GROSS_KG
    )


async def product_price(update, context):
    return await numeric_field(
        update, context, "product_price",
        "هزینه بسته‌بندی و کارگر به ازای هر کیلو، به تومان.\n"
        "Packaging & labor cost per KG, in Toman.\n\n"
        "مثال | Example: 3000",
        PRODUCT_PRICE
    )


async def pack_labor(update, context):
    return await numeric_field(
        update, context, "pack_labor",
        "حاشیه سود شما روی محصول به ازای هر کیلو، به تومان.\n"
        "Your product profit margin per KG, in Toman.\n\n"
        "مثال | Example: 6000",
        PACK_LABOR
    )


async def profit(update, context):
    return await numeric_field(
        update, context, "profit",
        "کرایه حمل زمینی تا بندرعباس، به تومان.\n"
        "Inland freight to Bandar Abbas, in Toman.\n\n"
        "مثال | Example: 55000000",
        PROFIT
    )


async def land(update, context):
    return await numeric_field(
        update, context, "land",
        "هزینه ترخیص، به تومان.\n"
        "Customs clearance cost, in Toman.\n\n"
        "مثال | Example: 600000000",
        LAND
    )


async def clearance(update, context):
    return await numeric_field(
        update, context, "clearance",
        "کرایه حمل دریایی، به دلار.\n"
        "Sea freight, in USD.\n\n"
        "مثال | Example: 8200",
        CLEARANCE
    )


async def sea(update, context):
    return await numeric_field(
        update, context, "sea_usd",
        "نرخ دلار به تومان.\n"
        "USD exchange rate in Toman.\n\n"
        "مثال | Example: 187000",
        SEA
    )


async def fx(update, context):
    return await numeric_field(
        update, context, "fx",
        "مقصد را وارد کنید.\n"
        "Enter destination.\n\n"
        "مثال | Example: ناواشیوا، هند | Nhava Sheva, India",
        FX
    )


def create_customer_pdf(data, result, path):
    """Customer-facing quotation. English only so no Persian font squares appear."""
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TTATitle", parent=styles["Title"], fontSize=19, leading=22,
        alignment=1, textColor=colors.white
    )
    subtitle = ParagraphStyle(
        "TTASubtitle", parent=styles["BodyText"], fontSize=10, leading=13,
        alignment=1
    )
    body = ParagraphStyle(
        "TTABody", parent=styles["BodyText"], fontSize=10, leading=14
    )
    small = ParagraphStyle(
        "TTASmall", parent=styles["BodyText"], fontSize=8.5, leading=12
    )
    big = ParagraphStyle(
        "TTABig", parent=styles["Title"], fontSize=27, leading=32,
        alignment=1
    )

    doc = SimpleDocTemplate(
        path, pagesize=A4, rightMargin=36, leftMargin=36,
        topMargin=30, bottomMargin=30
    )
    story = []

    logo_path = os.path.join(os.path.dirname(__file__), "tta_logo.png")
    header_data = []
    if os.path.exists(logo_path):
        from reportlab.platypus import Image as RLImage
        logo = RLImage(logo_path, width=58, height=58)
        header_data = [[logo, Paragraph(
            "<b>T.T.A EXPORT QUOTATION</b><br/>"
            "Tamana Tejarat Armaghan",
            title
        )]]
        header = Table(header_data, colWidths=[75, 445])
    else:
        header = Table([[
            Paragraph("T.T.A EXPORT QUOTATION", title)
        ]], colWidths=[520])

    header.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#17365D")),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 9),
        ("BOTTOMPADDING", (0,0), (-1,-1), 9),
    ]))
    story += [header, Spacer(1, 8)]

    company = Table([[
        Paragraph(
            "<b>TAMANA TEJARAT ARMAGHAN (T.T.A)</b><br/>"
            "No. 18, Pooneh Alley, Shahda-ye Shomali St., "
            "Molavi Building, 1st Floor, Unit 1, Bandar Abbas, Iran<br/>"
            "Mobile: +98 939 625 5418",
            subtitle
        )
    ]], colWidths=[520])
    company.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#D9EAF7")),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    story += [company, Spacer(1, 15)]

    rows = [
        ["Quotation No.", datetime.now().strftime("TTA-%Y%m%d-%H%M")],
        ["Date", datetime.now().strftime("%Y/%m/%d")],
        ["Customer", data.get("customer_name", "-")],
        ["Product", data["product"]],
        ["Packaging", data["packaging"]],
        ["Packages", money(to_decimal(data["packages"]), 0)],
        ["Gross Weight", f"{money(result['total_gross'], 2)} KG"],
        ["Destination", data["destination"]],
    ]
    table = Table(rows, colWidths=[170, 350])
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), .5, colors.HexColor("#B7B7B7")),
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#D9EAF7")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("FONTSIZE", (0,0), (-1,-1), 9.5),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story += [table, Spacer(1, 20)]

    offer = Table([
        [Paragraph("FINAL OFFER PRICE", body)],
        [Paragraph(f"{money(result['customer_price'], 2)} USD / KG", big)],
        [Paragraph(
            f"TOTAL SHIPMENT VALUE: {money(result['shipment_value'], 2)} USD",
            body
        )],
    ], colWidths=[520])
    offer.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#E2F0D9")),
        ("BOX", (0,0), (-1,-1), .8, colors.HexColor("#70AD47")),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ]))
    story += [offer, Spacer(1, 18)]

    story.append(Paragraph(
        "This quotation contains the final commercial offer only. "
        "Internal purchase costs, operating costs and profit margin are excluded.",
        small
    ))
    doc.build(story)


async def destination(update, context):
    context.user_data["destination"] = update.message.text.strip()
    await update.message.reply_text(
        "نام مشتری را وارد کنید.\n"
        "Enter customer name.\n\n"
        "Example: ABC Trading LLC"
    )
    return CUSTOMER


async def customer_name(update, context):
    context.user_data["customer_name"] = update.message.text.strip()

    data = context.user_data.copy()
    result = calculate(data)
    context.user_data["last_result"] = result

    text = (
        "🔐 محاسبه داخلی انجام شد | Internal calculation completed\n\n"
        f"هزینه تمام‌شده | Landed Cost: {money(result['cost_usd_kg'], 3)} USD/KG\n"
        f"قیمت نهایی مشتری | Final Customer Price: {money(result['customer_price'], 2)} USD/KG\n\n"
        "جزئیات خرید، بسته‌بندی، سود و سایر هزینه‌های داخلی "
        "در خروجی مشتری نمایش داده نمی‌شود."
    )

    keyboard = [
        [InlineKeyboardButton("📄 خروجی مشتری | Customer Quotation", callback_data="customer_offer")],
        [InlineKeyboardButton("🧮 محاسبه جدید | New Calculation", callback_data="new")],
        [InlineKeyboardButton("📋 نمایش فرمول | Show Formula", callback_data="formula")],
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "new":
        context.user_data.clear()
        await query.message.reply_text(
            "نام محصول را وارد کنید.\n"
            "Enter product name.\n\n"
            "مثال | Example: خرما | Dates"
        )
        return PRODUCT

    if query.data == "help":
        await query.message.reply_text(
            "📘 راهنما | Help\n\n"
            "این ربات برای محاسبه قیمت تمام‌شده صادرات طراحی شده است.\n"
            "This bot calculates export landed cost.\n\n"
            "مبنای وزن: ناخالص | Weight basis: Gross\n"
            "واحد قیمت داخلی: تومان | Local currency: Toman\n"
            "حمل دریایی: دلار | Sea freight: USD\n\n"
            "قیمت پیشنهادی مشتری به‌صورت خودکار محاسبه می‌شود."
        )
        return ConversationHandler.END

    if query.data == "customer_offer":
        data = context.user_data
        result = context.user_data.get("last_result")
        if not data.get("product") or not result:
            await query.message.reply_text(
                "ابتدا یک محاسبه انجام دهید.\nPlease complete a calculation first."
            )
            return ConversationHandler.END

        customer_text = (
            "📄 T.T.A EXPORT QUOTATION\n\n"
            f"Customer: {data.get('customer_name', '-')}\n"
            f"Product: {data['product']}\n"
            f"Packaging: {data['packaging']}\n"
            f"Packages: {money(to_decimal(data['packages']), 0)}\n"
            f"Gross Weight: {money(result['total_gross'], 2)} KG\n"
            f"Destination: {data['destination']}\n\n"
            f"FINAL OFFER PRICE: {money(result['customer_price'], 2)} USD/KG\n"
            f"TOTAL SHIPMENT VALUE: {money(result['shipment_value'], 2)} USD\n\n"
            "TAMANA TEJARAT ARMAGHAN (T.T.A)\n"
            "Bandar Abbas, Iran\n"
            "Mobile: +98 939 625 5418"
        )
        await query.message.reply_text(customer_text)

        pdf_path=f"/tmp/TTA_Customer_Quotation_{query.from_user.id}.pdf"
        create_customer_pdf(data, result, pdf_path)
        with open(pdf_path, "rb") as f:
            await query.message.reply_document(
                f, filename="TTA_Customer_Quotation.pdf",
                caption="📄 T.T.A Customer Quotation"
            )
        try:
            os.remove(pdf_path)
        except OSError:
            pass
        return ConversationHandler.END

    if query.data == "formula":
        await query.message.reply_text(
            "🧮 فرمول | Formula\n\n"
            "قیمت مبدأ / Origin Price =\n"
            "Product Price + Packaging & Labor + Product Profit\n\n"
            "وزن ناخالص کل / Total Gross Weight =\n"
            "Packages × Gross Weight per Package\n\n"
            "قیمت تمام‌شده دلاری / Landed Cost USD/KG =\n"
            "(Product Cost + Inland Freight + Customs + Sea Freight×FX)\n"
            "÷ Total Gross Weight ÷ FX\n\n"
            "Customer Price = Landed Cost rounded UP to $0.05"
        )
        return ConversationHandler.END


async def cancel(update, context):
    context.user_data.clear()
    await update.message.reply_text(
        "محاسبه لغو شد.\nCalculation cancelled.\n\n"
        "برای شروع دوباره /new را بزنید."
    )
    return ConversationHandler.END


def main():
    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing. "
            "Set it in Railway Variables or your hosting environment."
        )

    app = Application.builder().token(TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[
            CommandHandler("new", begin),
            CallbackQueryHandler(begin, pattern="^new$")
        ],
        states={
            PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, product)],
            PACKAGING: [MessageHandler(filters.TEXT & ~filters.COMMAND, packaging)],
            PACKAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, packages)],
            GROSS_KG: [MessageHandler(filters.TEXT & ~filters.COMMAND, gross)],
            PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_price)],
            PACK_LABOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, pack_labor)],
            PROFIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, profit)],
            LAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, land)],
            CLEARANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, clearance)],
            SEA: [MessageHandler(filters.TEXT & ~filters.COMMAND, sea)],
            FX: [MessageHandler(filters.TEXT & ~filters.COMMAND, fx)],
            DESTINATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, destination)],
            CUSTOMER: [MessageHandler(filters.TEXT & ~filters.COMMAND, customer_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conversation)
    app.add_handler(CallbackQueryHandler(buttons))

    log.info("TTA Export Calculator started.")
    app.run_polling()


if __name__ == "__main__":
    main()
