import os
import logging
import sqlite3
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
# T.T.A EXPORT CALCULATOR v5.2.0
# Multi-user / bilingual Telegram bot
#
# Environment variable required:
#   TELEGRAM_BOT_TOKEN
#
# User company profiles are stored in SQLite (tta_bot.db).
# Never put your Telegram bot token inside this file or GitHub.
# ============================================================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_PATH = os.getenv("TTA_DB_PATH", "tta_bot.db")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("tta-export-calculator")

(
    PRODUCT, PACKAGING, PACKAGES, GROSS_KG,
    PRODUCT_PRICE, PACK_LABOR, PROFIT,
    LAND, CLEARANCE, SEA, SWITCH_BILL, CROSS_STUFFING,
    FX, DESTINATION, CUSTOMER
) = range(15)

(
    PROFILE_COMPANY, PROFILE_ADDRESS, PROFILE_PHONE, PROFILE_LOGO
) = range(15, 19)


def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS company_profiles (
            user_id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT NOT NULL,
            logo_file_id TEXT
        )
    """)
    conn.commit()
    return conn


def get_profile(user_id):
    conn = db_connect()
    row = conn.execute(
        "SELECT company_name, address, phone, logo_file_id "
        "FROM company_profiles WHERE user_id = ?",
        (str(user_id),)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "company_name": row[0],
        "address": row[1],
        "phone": row[2],
        "logo_file_id": row[3],
    }


def save_profile(user_id, company_name, address, phone, logo_file_id=None):
    conn = db_connect()
    conn.execute("""
        INSERT INTO company_profiles (user_id, company_name, address, phone, logo_file_id)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            company_name=excluded.company_name,
            address=excluded.address,
            phone=excluded.phone,
            logo_file_id=excluded.logo_file_id
    """, (str(user_id), company_name, address, phone, logo_file_id))
    conn.commit()
    conn.close()


def to_decimal(value: str) -> Decimal:
    try:
        cleaned = str(value).replace(",", "").replace("٬", "").replace("٫", ".").strip()
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        raise ValueError("Invalid number")


def money(value: Decimal, decimals: int = 0) -> str:
    return f"{value:,.{decimals}f}"


def calculate(data):
    """Calculate export landed cost using GROSS WEIGHT as the basis."""
    packages = to_decimal(data["packages"])
    gross_per_package = to_decimal(data["gross_kg"])
    product_price = to_decimal(data["product_price"])
    pack_labor = to_decimal(data["pack_labor"])
    profit = to_decimal(data["profit"])
    land = to_decimal(data["land"])
    clearance = to_decimal(data["clearance"])
    sea_usd = to_decimal(data["sea_usd"])
    switch_bill_usd = to_decimal(data.get("switch_bill_usd", "0"))
    cross_stuffing_usd = to_decimal(data.get("cross_stuffing_usd", "0"))
    fx = to_decimal(data["fx"])

    if packages <= 0 or gross_per_package <= 0 or fx <= 0:
        raise ValueError("Packages, gross weight and FX rate must be greater than zero")

    total_gross = packages * gross_per_package
    origin_price_kg = product_price + pack_labor + profit
    product_total = total_gross * origin_price_kg

    extra_freight_usd = sea_usd + switch_bill_usd + cross_stuffing_usd
    freight_local = extra_freight_usd * fx
    export_total = land + clearance + freight_local
    total_cost = product_total + export_total

    cost_local_kg = total_cost / total_gross
    cost_usd_kg = cost_local_kg / fx

    # Automatic customer price: round UP to the next $0.05.
    step = Decimal("0.05")
    customer_price = (cost_usd_kg / step).to_integral_value(rounding=ROUND_UP) * step

    return {
        "total_gross": total_gross,
        "origin_price_kg": origin_price_kg,
        "product_total": product_total,
        "extra_freight_usd": extra_freight_usd,
        "freight_local": freight_local,
        "export_total": export_total,
        "total_cost": total_cost,
        "cost_local_kg": cost_local_kg,
        "cost_usd_kg": cost_usd_kg,
        "customer_price": customer_price,
        "shipment_value": customer_price * total_gross,
    }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    profile = get_profile(update.effective_user.id)

    keyboard = [
        [InlineKeyboardButton("🧮 محاسبه جدید | New Calculation", callback_data="new")],
        [InlineKeyboardButton("🏢 مشخصات شرکت | Company Profile", callback_data="profile")],
        [InlineKeyboardButton("ℹ️ راهنما | Help", callback_data="help")],
    ]

    status = "پروفایل شرکت تنظیم شده است." if profile else "ابتدا پروفایل شرکت خود را تنظیم کنید."
    await update.message.reply_text(
        "🇮🇷 T.T.A Export Calculator 🇬🇧\n\n"
        "محاسبه قیمت تمام‌شده صادرات برای محصولات مختلف.\n"
        "Export landed-cost calculator for different products.\n\n"
        "خرما | Dates • سیب | Apples • کیوی | Kiwi • انجیر | Figs • "
        "کشمش | Raisins • ...\n\n"
        f"{status}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def begin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        message = update.callback_query.message
        user_id = update.effective_user.id
    else:
        message = update.message
        user_id = update.effective_user.id

    profile = get_profile(user_id)
    if not profile:
        await message.reply_text(
            "🏢 قبل از محاسبه باید مشخصات شرکت خود را ثبت کنید.\n"
            "Before calculating, please set your company profile.\n\n"
            "از دکمه Company Profile یا دستور /profile استفاده کنید."
        )
        return ConversationHandler.END

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
        await update.message.reply_text("لطفاً مقدار را وارد کنید.\nPlease enter a value.")
        return next_state - 1
    context.user_data[key] = value
    await update.message.reply_text(prompt)
    return next_state


async def numeric_field(update, context, key, prompt, current_state):
    try:
        value = to_decimal(update.message.text)
        if value < 0:
            raise ValueError("negative")
    except ValueError:
        await update.message.reply_text(
            "❌ عدد نامعتبر است.\n"
            "Please enter a valid non-negative number.\n\n"
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
        "هزینه Switch Bill of Lading را به دلار وارد کنید.\n"
        "Enter Switch Bill of Lading cost in USD.\n\n"
        "اگر نیاز نیست، 0 وارد کنید. | If not applicable, enter 0.\n"
        "مثال | Example: 150",
        SEA
    )


async def switch_bill(update, context):
    return await numeric_field(
        update, context, "switch_bill_usd",
        "هزینه Cross Stuffing را به دلار وارد کنید.\n"
        "Enter Cross Stuffing cost in USD.\n\n"
        "اگر نیاز نیست، 0 وارد کنید. | If not applicable, enter 0.\n"
        "مثال | Example: 300",
        SWITCH_BILL
    )


async def cross_stuffing(update, context):
    return await numeric_field(
        update, context, "cross_stuffing_usd",
        "نرخ دلار به تومان.\n"
        "USD exchange rate in Toman.\n\n"
        "مثال | Example: 187000",
        CROSS_STUFFING
    )


async def fx(update, context):
    return await numeric_field(
        update, context, "fx",
        "مقصد را وارد کنید.\n"
        "Enter destination.\n\n"
        "مثال | Example: ناواشیوا، هند | Nhava Sheva, India",
        FX
    )


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
    try:
        result = calculate(data)
    except Exception as exc:
        log.exception("Calculation error: %s", exc)
        await update.message.reply_text(
            "❌ محاسبه انجام نشد. لطفاً اطلاعات را بررسی کنید.\n"
            "Calculation failed. Please check the entered values."
        )
        return ConversationHandler.END

    context.user_data["last_result"] = result

    text = (
        "🔐 محاسبه داخلی انجام شد | Internal calculation completed\n\n"
        f"هزینه تمام‌شده | Landed Cost: {money(result['cost_usd_kg'], 3)} USD/KG\n"
        f"قیمت نهایی مشتری | Final Customer Price: {money(result['customer_price'], 2)} USD/KG\n\n"
        "قیمت‌های خرید، بسته‌بندی، سود و هزینه‌های داخلی در خروجی مشتری نمایش داده نمی‌شوند."
    )

    keyboard = [
        [InlineKeyboardButton("📄 خروجی مشتری | Customer Quotation", callback_data="customer_offer")],
        [InlineKeyboardButton("🧮 محاسبه جدید | New Calculation", callback_data="new")],
        [InlineKeyboardButton("📋 نمایش فرمول | Show Formula", callback_data="formula")],
    ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


async def profile_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        message = update.callback_query.message
    else:
        message = update.message

    context.user_data.clear()
    await message.reply_text(
        "🏢 Company Profile | مشخصات شرکت\n\n"
        "نام شرکت را وارد کنید.\n"
        "Enter your company name.\n\n"
        "Example: ABC Trading Company"
    )
    return PROFILE_COMPANY


async def profile_company(update, context):
    value = update.message.text.strip()
    if not value:
        await update.message.reply_text("لطفاً نام شرکت را وارد کنید.")
        return PROFILE_COMPANY
    context.user_data["profile_company"] = value
    await update.message.reply_text(
        "آدرس شرکت را به انگلیسی وارد کنید.\n"
        "Enter your company address in English.\n\n"
        "Example: Bandar Abbas, Iran"
    )
    return PROFILE_ADDRESS


async def profile_address(update, context):
    value = update.message.text.strip()
    if not value:
        await update.message.reply_text("لطفاً آدرس شرکت را وارد کنید.")
        return PROFILE_ADDRESS
    context.user_data["profile_address"] = value
    await update.message.reply_text(
        "شماره تماس شرکت را وارد کنید.\n"
        "Enter company phone / WhatsApp number.\n\n"
        "Example: +98 939 625 5418"
    )
    return PROFILE_PHONE


async def profile_phone(update, context):
    value = update.message.text.strip()
    if not value:
        await update.message.reply_text("لطفاً شماره تماس را وارد کنید.")
        return PROFILE_PHONE
    context.user_data["profile_phone"] = value
    await update.message.reply_text(
        "لوگوی شرکت را به‌صورت عکس ارسال کنید.\n"
        "Send your company logo as an image.\n\n"
        "اگر لوگو ندارید یا نمی‌خواهید نمایش داده شود، کلمه SKIP را بفرستید."
    )
    return PROFILE_LOGO


async def profile_logo(update, context):
    logo_file_id = None
    if update.message.photo:
        logo_file_id = update.message.photo[-1].file_id
    elif update.message.text and update.message.text.strip().lower() in {"skip", "no", "ندارم", "خیر"}:
        logo_file_id = None
    else:
        await update.message.reply_text(
            "لطفاً لوگو را به‌صورت عکس ارسال کنید یا SKIP را بفرستید.\n"
            "Send an image or type SKIP."
        )
        return PROFILE_LOGO

    save_profile(
        update.effective_user.id,
        context.user_data["profile_company"],
        context.user_data["profile_address"],
        context.user_data["profile_phone"],
        logo_file_id,
    )
    context.user_data.clear()

    await update.message.reply_text(
        "✅ Company Profile saved successfully.\n"
        "پروفایل شرکت با موفقیت ذخیره شد.\n\n"
        "از این پس Customer Quotation با مشخصات شرکت خودتان صادر می‌شود."
    )
    return ConversationHandler.END


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "profile":
        # Profile conversation entry point handles this callback.
        return PROFILE_COMPANY

    if query.data == "new":
        profile = get_profile(update.effective_user.id)
        if not profile:
            await query.message.reply_text(
                "ابتدا Company Profile را تنظیم کنید.\n"
                "Please set your Company Profile first."
            )
            return ConversationHandler.END
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
            "حمل دریایی، Switch Bill و Cross Stuffing: دلار | USD\n\n"
            "قیمت پیشنهادی مشتری به‌صورت خودکار محاسبه می‌شود.\n"
            "Customer price is calculated automatically.\n\n"
            "هر کاربر می‌تواند مشخصات شرکت و لوگوی خودش را ثبت کند."
        )
        return ConversationHandler.END

    if query.data == "customer_offer":
        data = context.user_data
        result = context.user_data.get("last_result")
        profile = get_profile(update.effective_user.id)

        if not data.get("product") or not result or not profile:
            await query.message.reply_text(
                "ابتدا پروفایل و محاسبه را کامل کنید.\n"
                "Please complete your profile and calculation first."
            )
            return ConversationHandler.END

        customer_text = (
            "📄 EXPORT QUOTATION\n\n"
            f"Customer: {data.get('customer_name', '-')}\n"
            f"Product: {data['product']}\n"
            f"Packaging: {data['packaging']}\n"
            f"Packages: {money(to_decimal(data['packages']), 0)}\n"
            f"Gross Weight: {money(result['total_gross'], 2)} KG\n"
            f"Destination: {data['destination']}\n\n"
            f"FINAL OFFER PRICE: {money(result['customer_price'], 2)} USD/KG\n"
            f"TOTAL SHIPMENT VALUE: {money(result['shipment_value'], 2)} USD\n\n"
            f"{profile['company_name']}\n"
            f"{profile['address']}\n"
            f"Mobile: {profile['phone']}"
        )
        await query.message.reply_text(customer_text)

        logo_path = None
        if profile.get("logo_file_id"):
            try:
                tg_file = await context.bot.get_file(profile["logo_file_id"])
                logo_path = f"/tmp/tta_logo_{query.from_user.id}.png"
                await tg_file.download_to_drive(logo_path)
            except Exception:
                log.exception("Could not download company logo")
                logo_path = None

        pdf_path = f"/tmp/TTA_Customer_Quotation_{query.from_user.id}.pdf"
        create_customer_pdf(data, result, profile, pdf_path, logo_path)
        with open(pdf_path, "rb") as f:
            await query.message.reply_document(
                f,
                filename="Export_Quotation.pdf",
                caption="📄 Customer Quotation"
            )

        for path in (pdf_path, logo_path):
            if path:
                try:
                    os.remove(path)
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
            "Export Freight USD =\n"
            "Sea Freight + Switch Bill + Cross Stuffing\n\n"
            "Landed Cost USD/KG =\n"
            "(Product Cost + Inland Freight + Customs + Export Freight×FX)\n"
            "÷ Total Gross Weight ÷ FX\n\n"
            "Customer Price = Landed Cost rounded UP to $0.05"
        )
        return ConversationHandler.END

    return ConversationHandler.END


def create_customer_pdf(data, result, profile, path, logo_path=None):
    """Customer-facing quotation. English only; internal costs are excluded."""
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TTATitle", parent=styles["Title"], fontSize=18, leading=21,
        alignment=1, textColor=colors.white
    )
    subtitle = ParagraphStyle(
        "TTASubtitle", parent=styles["BodyText"], fontSize=9.5, leading=12,
        alignment=1
    )
    body = ParagraphStyle(
        "TTABody", parent=styles["BodyText"], fontSize=9.5, leading=13
    )
    small = ParagraphStyle(
        "TTASmall", parent=styles["BodyText"], fontSize=8.5, leading=11
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

    header_cells = []
    if logo_path and os.path.exists(logo_path):
        from reportlab.platypus import Image as RLImage
        logo = RLImage(logo_path, width=62, height=62, kind="proportional")
        header_cells.append(logo)
    header_cells.append(Paragraph("<b>EXPORT QUOTATION</b>", title))
    col_widths = [78, 442] if len(header_cells) == 2 else [520]
    header = Table([header_cells], colWidths=col_widths)
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
            f"<b>{profile['company_name']}</b><br/>"
            f"{profile['address']}<br/>"
            f"Mobile: {profile['phone']}",
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
        "Internal purchase costs, operating costs, profit margin and logistics breakdown are excluded.",
        small
    ))
    doc.build(story)


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

    profile_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("profile", profile_start),
            CallbackQueryHandler(profile_start, pattern="^profile$")
        ],
        states={
            PROFILE_COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_company)],
            PROFILE_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_address)],
            PROFILE_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_phone)],
            PROFILE_LOGO: [
                MessageHandler(filters.PHOTO, profile_logo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, profile_logo),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    calculation_conversation = ConversationHandler(
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
            SWITCH_BILL: [MessageHandler(filters.TEXT & ~filters.COMMAND, switch_bill)],
            CROSS_STUFFING: [MessageHandler(filters.TEXT & ~filters.COMMAND, cross_stuffing)],
            FX: [MessageHandler(filters.TEXT & ~filters.COMMAND, fx)],
            DESTINATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, destination)],
            CUSTOMER: [MessageHandler(filters.TEXT & ~filters.COMMAND, customer_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(profile_conversation)
    app.add_handler(calculation_conversation)
    app.add_handler(CallbackQueryHandler(buttons))

    log.info("TTA Export Calculator v5.2.0 started.")
    app.run_polling()


if __name__ == "__main__":
    main()
