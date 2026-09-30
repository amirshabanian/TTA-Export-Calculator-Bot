# T.T.A EXPORT CALCULATOR v6.0.3
# Professional bilingual Telegram export-cost calculator
# 7-day trial + per-user licenses + admin panel + bilingual calculation flow

import os
import logging
import sqlite3
import secrets
import string
from decimal import Decimal, InvalidOperation, ROUND_UP
from datetime import datetime, timedelta, timezone

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)

VERSION = "6.0.3"
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_PATH = os.getenv("TTA_DB_PATH", "tta_bot.db")
TRIAL_DAYS = int(os.getenv("TTA_TRIAL_DAYS", "7"))
ADMIN_IDS = {x.strip() for x in os.getenv("TTA_ADMIN_IDS", "").split(",") if x.strip()}

CREATOR_NAME = os.getenv("TTA_CREATOR_NAME", "Amir Shabanian")
CREATOR_PHONE = os.getenv("TTA_CREATOR_PHONE", "")
CREATOR_WHATSAPP = os.getenv("TTA_CREATOR_WHATSAPP", "")
CREATOR_TELEGRAM = os.getenv("TTA_CREATOR_TELEGRAM", "")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("tta-export-calculator")

(
    PRODUCT, PACKAGING, PACKAGES, GROSS_KG, NET_KG,
    PRODUCT_PRICE, PACK_LABOR, PROFIT, LAND, CLEARANCE,
    SEA, SEA_PAYMENT, TEHRAN_TAX, UAE_AED_RATE,
    SWITCH_BILL, CROSS_STUFFING, FX, DESTINATION, CUSTOMER,
) = range(19)
PROFILE_COMPANY, PROFILE_ADDRESS, PROFILE_PHONE, PROFILE_LOGO = range(19, 23)


def now_utc():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat() if dt else None


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except ValueError:
        return None


def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS company_profiles(
        user_id TEXT PRIMARY KEY, company_name TEXT NOT NULL,
        address TEXT NOT NULL, phone TEXT NOT NULL, logo_file_id TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id TEXT PRIMARY KEY, username TEXT, first_name TEXT,
        status TEXT NOT NULL DEFAULT 'TRIAL',
        trial_start TEXT, trial_end TEXT, created_at TEXT NOT NULL,
        last_seen TEXT NOT NULL, license_key TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS licenses(
        license_key TEXT PRIMARY KEY, duration_days INTEGER,
        permanent INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'UNUSED', user_id TEXT,
        customer_name TEXT, created_at TEXT NOT NULL,
        activated_at TEXT, expires_at TEXT)""")
    conn.commit()
    return conn


def is_admin(user_id):
    return str(user_id) in ADMIN_IDS


def ensure_user(tg_user):
    uid = str(tg_user.id)
    conn = db_connect()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    now = now_utc()
    if not row:
        trial_start = now
        trial_end = now + timedelta(days=TRIAL_DAYS)
        conn.execute("""INSERT INTO users
            (user_id,username,first_name,status,trial_start,trial_end,created_at,last_seen)
            VALUES(?,?,?,?,?,?,?,?)""",
            (uid, tg_user.username or "", tg_user.first_name or "",
             "TRIAL", iso(trial_start), iso(trial_end), iso(now), iso(now)))
    else:
        conn.execute("UPDATE users SET username=?,first_name=?,last_seen=? WHERE user_id=?",
                     (tg_user.username or "", tg_user.first_name or "", iso(now), uid))
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return row


def get_user(user_id):
    conn = db_connect()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (str(user_id),)).fetchone()
    conn.close()
    return row


def get_profile(user_id):
    conn = db_connect()
    row = conn.execute(
        "SELECT company_name,address,phone,logo_file_id FROM company_profiles WHERE user_id=?",
        (str(user_id),)).fetchone()
    conn.close()
    return dict(row) if row else None


def save_profile(user_id, company_name, address, phone, logo_file_id=None):
    conn = db_connect()
    conn.execute("""INSERT INTO company_profiles(user_id,company_name,address,phone,logo_file_id)
        VALUES(?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET
        company_name=excluded.company_name,address=excluded.address,
        phone=excluded.phone,logo_file_id=excluded.logo_file_id""",
        (str(user_id), company_name, address, phone, logo_file_id))
    conn.commit()
    conn.close()


def access_state(user_id):
    if is_admin(user_id):
        return "ADMIN", None
    row = get_user(user_id)
    if not row:
        return "TRIAL", now_utc() + timedelta(days=TRIAL_DAYS)
    if row["license_key"]:
        conn = db_connect()
        lic = conn.execute("SELECT * FROM licenses WHERE license_key=?",
                           (row["license_key"],)).fetchone()
        conn.close()
        if lic and lic["status"] == "ACTIVE":
            exp = parse_dt(lic["expires_at"])
            if lic["permanent"] or (exp and exp > now_utc()):
                return "LICENSE", exp
    exp = parse_dt(row["trial_end"])
    if exp and exp > now_utc():
        return "TRIAL", exp
    return "EXPIRED", exp


def access_allowed(user_id):
    return access_state(user_id)[0] in {"ADMIN", "TRIAL", "LICENSE"}


def access_message(user_id):
    state, exp = access_state(user_id)
    if state == "ADMIN":
        return "👑 Administrator access | دسترسی مدیر"
    if state == "LICENSE":
        if exp:
            return f"🔐 License active | لایسنس فعال — تا {exp.astimezone().strftime('%Y/%m/%d')}"
        return "🔐 Permanent License | لایسنس دائمی"
    if state == "TRIAL":
        seconds = max(0, int((exp - now_utc()).total_seconds())) if exp else 0
        days = (seconds + 86399) // 86400
        return f"🎁 7-Day Trial | تست رایگان — {days} day(s) remaining"
    return "🔒 Trial expired | دوره آزمایشی تمام شده است"


def generate_license_key():
    alphabet = string.ascii_uppercase + string.digits
    while True:
        raw = "".join(secrets.choice(alphabet) for _ in range(16))
        key = "TTA-" + "-".join(raw[i:i+4] for i in range(0, 16, 4))
        conn = db_connect()
        exists = conn.execute("SELECT 1 FROM licenses WHERE license_key=?", (key,)).fetchone()
        conn.close()
        if not exists:
            return key


def create_license(duration_days=None, permanent=False):
    key = generate_license_key()
    created = now_utc()
    expires = None if permanent else created + timedelta(days=duration_days)
    conn = db_connect()
    conn.execute("""INSERT INTO licenses
        (license_key,duration_days,permanent,status,created_at,expires_at)
        VALUES(?,?,?,?,?,?)""",
        (key, duration_days, 1 if permanent else 0, "UNUSED", iso(created), iso(expires)))
    conn.commit()
    conn.close()
    return key, expires


def activate_license(user_id, key):
    key = key.strip().upper().replace(" ", "")
    conn = db_connect()
    lic = conn.execute("SELECT * FROM licenses WHERE license_key=?", (key,)).fetchone()
    if not lic:
        conn.close()
        return False, "❌ License not found | لایسنس پیدا نشد."
    if lic["status"] != "UNUSED":
        conn.close()
        return False, "❌ This license is already used or unavailable."
    activated = now_utc()
    expires = None if lic["permanent"] else activated + timedelta(days=lic["duration_days"] or 0)
    conn.execute("""UPDATE licenses SET status='ACTIVE',user_id=?,
        activated_at=?,expires_at=? WHERE license_key=?""",
        (str(user_id), iso(activated), iso(expires), key))
    conn.execute("UPDATE users SET status='LICENSE',license_key=? WHERE user_id=?",
                 (key, str(user_id)))
    conn.commit()
    conn.close()
    return True, "✅ License activated successfully | لایسنس با موفقیت فعال شد."


def admin_stats():
    conn = db_connect()
    now = iso(now_utc())
    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    trials = conn.execute(
        "SELECT COUNT(*) FROM users WHERE status='TRIAL' AND trial_end > ?", (now,)).fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM licenses WHERE status='ACTIVE'").fetchone()[0]
    unused = conn.execute("SELECT COUNT(*) FROM licenses WHERE status='UNUSED'").fetchone()[0]
    expired = conn.execute(
        "SELECT COUNT(*) FROM users WHERE trial_end <= ? AND (license_key IS NULL OR license_key='')",
        (now,)).fetchone()[0]
    conn.close()
    return total, trials, active, unused, expired


def to_decimal(value):
    try:
        return Decimal(str(value).replace(",", "").replace("٬", "").replace("٫", ".").strip())
    except (InvalidOperation, ValueError):
        raise ValueError("Invalid number")


def money(value, decimals=0):
    return f"{value:,.{decimals}f}"


def calculate(data):
    packages = to_decimal(data["packages"])
    gross = to_decimal(data["gross_kg"])
    net = to_decimal(data["net_kg"])
    product = to_decimal(data["product_price"])
    pack = to_decimal(data["pack_labor"])
    profit = to_decimal(data["profit"])
    land = to_decimal(data["land"])
    clearance = to_decimal(data["clearance"])
    sea = to_decimal(data["sea_usd"])
    fx = to_decimal(data["fx"])
    tax = to_decimal(data.get("tehran_tax_pct", "3"))
    aed = to_decimal(data.get("uae_aed_rate", "3.685"))
    switch = to_decimal(data.get("switch_bill_usd", "0"))
    cross = to_decimal(data.get("cross_stuffing_usd", "0"))
    method = data.get("sea_payment_method", "tehran")

    if packages <= 0 or gross <= 0 or net <= 0 or net > gross or fx <= 0:
        raise ValueError("Invalid package/weight/FX values")

    total_gross = packages * gross
    total_net = packages * net
    origin = product + pack + profit
    product_total = total_gross * origin

    effective_sea = sea * (Decimal("1") + tax / Decimal("100")) if method == "tehran" else sea
    sea_aed = sea * aed if method == "uae" else Decimal("0")
    freight_usd = effective_sea + switch + cross
    total_cost = product_total + land + clearance + freight_usd * fx
    cost_usd = (total_cost / total_gross) / fx

    step = Decimal("0.05")
    offer = (cost_usd / step).to_integral_value(rounding=ROUND_UP) * step

    return {
        "total_gross": total_gross,
        "total_net": total_net,
        "origin_price_kg": origin,
        "product_total": product_total,
        "sea_payment_method": method,
        "tehran_tax_pct": tax,
        "uae_aed_rate": aed,
        "sea_effective_usd": effective_sea,
        "sea_aed_amount": sea_aed,
        "extra_freight_usd": freight_usd,
        "total_cost": total_cost,
        "cost_usd_kg": cost_usd,
        "customer_price": offer,
        "shipment_value": offer * total_gross,
    }


def main_keyboard(user_id):
    rows = [
        [InlineKeyboardButton("🧮 محاسبه جدید | New Calculation", callback_data="new")],
        [InlineKeyboardButton("🏢 پروفایل شرکت | Company Profile", callback_data="profile")],
        [InlineKeyboardButton("🔐 لایسنس | License", callback_data="license")],
        [
            InlineKeyboardButton("📞 ارتباط | Contact", callback_data="contact"),
            InlineKeyboardButton("ℹ️ راهنما | Help", callback_data="help"),
        ],
    ]
    if is_admin(user_id):
        rows.insert(0, [InlineKeyboardButton("👑 پنل مدیریت | Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(rows)


async def start(update, context):
    context.user_data.clear()
    ensure_user(update.effective_user)
    await update.message.reply_text(
        f"🌿 <b>T.T.A EXPORT CALCULATOR</b>\n"
        f"<b>Version {VERSION}</b>\n\n"
        f"{access_message(update.effective_user.id)}\n\n"
        "محاسبه حرفه‌ای قیمت تمام‌شده صادرات و صدور Customer Quotation.\n"
        "Professional export landed-cost calculation & quotation.",
        parse_mode="HTML",
        reply_markup=main_keyboard(update.effective_user.id),
    )


async def license_menu(update, context):
    q = update.callback_query
    await q.answer()
    state, exp = access_state(q.from_user.id)
    txt = "🔐 <b>LICENSE CENTER | مرکز لایسنس</b>\n\n"
    if state == "TRIAL":
        txt += f"🎁 Trial active | تست فعال\nExpires: {exp.astimezone().strftime('%Y/%m/%d %H:%M')}\n\n"
    elif state == "LICENSE":
        txt += "🟢 License active | لایسنس فعال است.\n\n"
    elif state == "EXPIRED":
        txt += "🔴 Trial expired | دوره آزمایشی تمام شده است.\n\n"
    elif state == "ADMIN":
        txt += "👑 Administrator | مدیر سیستم\n\n"
    txt += "اگر لایسنس دریافت کرده‌اید، کد را وارد کنید.\nIf you received a license, enter your key."
    await q.message.reply_text(
        txt, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔑 ورود License Key", callback_data="enter_license")],
            [InlineKeyboardButton("🏠 منوی اصلی | Main Menu", callback_data="home")],
        ]),
    )


async def enter_license_prompt(update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["awaiting_license"] = True
    await q.message.reply_text(
        "🔑 <b>License Key</b>\nکد لایسنس را ارسال کنید.\n"
        "Example: <code>TTA-ABCD-EFGH-IJKL</code>",
        parse_mode="HTML",
    )


async def handle_license_text(update, context):
    if not context.user_data.get("awaiting_license"):
        return False
    context.user_data.pop("awaiting_license", None)
    _, msg = activate_license(update.effective_user.id, update.message.text)
    await update.message.reply_text(msg, reply_markup=main_keyboard(update.effective_user.id))
    return True


async def creator_contact(update, context):
    q = update.callback_query
    if q:
        await q.answer()
        msg = q.message
    else:
        msg = update.message
    lines = ["📞 <b>ارتباط با سازنده | Contact</b>", "", f"👤 {CREATOR_NAME}"]
    if CREATOR_PHONE:
        lines.append(f"📱 {CREATOR_PHONE}")
    if CREATOR_WHATSAPP:
        lines.append(f"💬 WhatsApp: {CREATOR_WHATSAPP}")
    if CREATOR_TELEGRAM:
        lines.append(f"✈️ Telegram: {CREATOR_TELEGRAM}")
    await msg.reply_text(
        "\n".join(lines), parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🏠 منوی اصلی | Main Menu", callback_data="home")]]
        ),
    )


HELP_TEXT = (
    "📘 <b>راهنما | Help</b>\n\n"
    "1️⃣ Gross Weight = مبنای محاسبه قیمت است.\n"
    "2️⃣ Net Weight فقط برای اطلاعات و Quotation ثبت می‌شود.\n"
    "3️⃣ قیمت نهایی مشتری خودکار محاسبه و رو به بالا تا $0.05 گرد می‌شود.\n"
    "4️⃣ هر Telegram ID فقط یک Trial هفت‌روزه دارد.\n"
    "5️⃣ پس از پایان Trial، برای ادامه License لازم است."
)


async def help_command(update, context):
    ensure_user(update.effective_user)
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🏠 منوی اصلی | Main Menu", callback_data="home")]]
        ),
    )


async def help_menu(update, context):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(
        HELP_TEXT, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🏠 منوی اصلی | Main Menu", callback_data="home")]]
        ),
    )


async def license_command(update, context):
    ensure_user(update.effective_user)
    state, exp = access_state(update.effective_user.id)
    txt = "🔐 LICENSE CENTER | مرکز لایسنس\n\n"
    if state == "TRIAL":
        txt += f"🎁 Trial active | تست فعال\nExpires: {exp.astimezone().strftime('%Y/%m/%d %H:%M')}\n\n"
    elif state == "LICENSE":
        txt += "🟢 License active | لایسنس فعال است.\n\n"
    elif state == "EXPIRED":
        txt += "🔴 Trial expired | دوره آزمایشی تمام شده است.\n\n"
    elif state == "ADMIN":
        txt += "👑 Administrator | مدیر سیستم\n\n"
    txt += "برای فعال‌سازی، License Key را ارسال کنید."
    await update.message.reply_text(
        txt,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔑 ورود License Key", callback_data="enter_license")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="home")],
        ]),
    )


async def begin(update, context):
    ensure_user(update.effective_user)
    msg = update.callback_query.message if update.callback_query else update.message
    if not access_allowed(update.effective_user.id):
        await msg.reply_text(
            "🔒 Trial expired | دوره آزمایشی شما تمام شده است.\n"
            "از بخش License یک کد معتبر وارد کنید.",
            reply_markup=main_keyboard(update.effective_user.id),
        )
        return ConversationHandler.END
    if not get_profile(update.effective_user.id):
        await msg.reply_text(
            "🏢 ابتدا Company Profile را تکمیل کنید.\n"
            "Please complete your Company Profile first.",
            reply_markup=main_keyboard(update.effective_user.id),
        )
        return ConversationHandler.END
    if update.callback_query:
        await update.callback_query.answer()
    context.user_data.clear()
    await msg.reply_text(
        "📦 <b>STEP 1/19 — Product</b>\n\n"
        "نوع / نام محصول را وارد کنید.\n"
        "Enter product name / type.\n\n"
        "مثال / Example: <b>Dates / خرما</b>",
        parse_mode="HTML",
    )
    return PRODUCT


async def text_field(update, context, key, prompt, state):
    value = update.message.text.strip()
    if not value:
        await update.message.reply_text("❌ لطفاً مقدار را وارد کنید.")
        return state
    context.user_data[key] = value
    await update.message.reply_text(prompt, parse_mode="HTML")
    return state


async def numeric_field(update, context, key, prompt, state, minimum=0):
    try:
        value = to_decimal(update.message.text)
        if value < Decimal(str(minimum)):
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ عدد نامعتبر است.\nPlease enter a valid number."
        )
        return state
    context.user_data[key] = update.message.text.strip()
    await update.message.reply_text(prompt, parse_mode="HTML")
    return state


async def product(update, c):
    return await text_field(
        update, c, "product",
        "📦 <b>STEP 2/19 — Packaging</b>\n\n"
        "نوع بسته‌بندی را وارد کنید.\nEnter packaging type.\n\n"
        "مثال / Example: <b>Carton / کارتن</b>",
        PACKAGING,
    )


async def packaging(update, c):
    return await text_field(
        update, c, "packaging",
        "🔢 <b>STEP 3/19 — Number of Packages</b>\n\n"
        "تعداد کل بسته‌ها را وارد کنید.\nEnter total number of packages.\n\n"
        "مثال / Example: <b>3500</b>",
        PACKAGES,
    )


async def packages(update, c):
    return await numeric_field(
        update, c, "packages",
        "⚖️ <b>STEP 4/19 — Gross Weight / بسته</b>\n\n"
        "وزن ناخالص هر بسته را به KG وارد کنید.\n"
        "Enter gross weight per package in KG.\n\n"
        "مثال / Example: <b>6.800 KG</b>",
        GROSS_KG, minimum=Decimal("0.000001"),
    )


async def gross(update, c):
    return await numeric_field(
        update, c, "gross_kg",
        "⚖️ <b>STEP 5/19 — Net Weight / بسته</b>\n\n"
        "وزن خالص هر بسته را به KG وارد کنید.\n"
        "Enter net weight per package in KG.\n\n"
        "مثال / Example: <b>6.500 KG</b>",
        NET_KG, minimum=Decimal("0.000001"),
    )


async def net(update, c):
    try:
        value = to_decimal(update.message.text)
        gross_value = to_decimal(c.user_data.get("gross_kg", "0"))
        if value <= 0 or gross_value <= 0 or value > gross_value:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ وزن خالص نامعتبر است.\n"
            "باید بیشتر از صفر و حداکثر برابر وزن ناخالص باشد.\n\n"
            "❌ Invalid net weight. It must be > 0 and ≤ gross weight."
        )
        return NET_KG
    c.user_data["net_kg"] = update.message.text.strip()
    await update.message.reply_text(
        "💰 <b>STEP 6/19 — Product Purchase Price</b>\n\n"
        "قیمت خرید محصول به ازای هر KG، به تومان را وارد کنید.\n"
        "Enter product purchase price per KG in Toman.\n\n"
        "مثال / Example: <b>133000</b>",
        parse_mode="HTML",
    )
    return PRODUCT_PRICE


async def product_price(update, c):
    return await numeric_field(
        update, c, "product_price",
        "📦 <b>STEP 7/19 — Packaging & Labor</b>\n\n"
        "هزینه بسته‌بندی و کارگر به ازای هر KG، به تومان را وارد کنید.\n"
        "Enter packaging & labor cost per KG in Toman.\n\n"
        "مثال / Example: <b>3000</b>",
        PACK_LABOR,
    )


async def pack_labor(update, c):
    return await numeric_field(
        update, c, "pack_labor",
        "📈 <b>STEP 8/19 — Profit Margin</b>\n\n"
        "حاشیه سود محصول به ازای هر KG، به تومان را وارد کنید.\n"
        "Enter product profit margin per KG in Toman.\n\n"
        "مثال / Example: <b>6000</b>",
        PROFIT,
    )


async def profit(update, c):
    return await numeric_field(
        update, c, "profit",
        "🚚 <b>STEP 9/19 — Inland Freight</b>\n\n"
        "هزینه حمل زمینی تا بندرعباس، به تومان را وارد کنید.\n"
        "Enter inland freight to Bandar Abbas in Toman.",
        LAND,
    )


async def land(update, c):
    return await numeric_field(
        update, c, "land",
        "🛃 <b>STEP 10/19 — Customs Clearance</b>\n\n"
        "هزینه ترخیص، به تومان را وارد کنید.\n"
        "Enter customs clearance cost in Toman.",
        CLEARANCE,
    )


async def clearance(update, c):
    return await numeric_field(
        update, c, "clearance",
        "🚢 <b>STEP 11/19 — Sea Freight</b>\n\n"
        "هزینه حمل دریایی را به USD وارد کنید.\n"
        "Enter sea freight in USD.",
        SEA,
    )


async def sea(update, c):
    try:
        value = to_decimal(update.message.text)
        if value < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ عدد نامعتبر است. / Invalid number.")
        return SEA
    c.user_data["sea_usd"] = update.message.text.strip()
    await update.message.reply_text(
        "💳 <b>STEP 12/19 — Sea Freight Payment Method</b>\n\n"
        "روش پرداخت حمل دریایی را انتخاب کنید:\n"
        "Select payment method:\n\n"
        "1️⃣ تهران — USD + 3% Tax\n"
        "2️⃣ UAE — AED\n\n"
        "فقط 1 یا 2 را ارسال کنید. / Send 1 or 2.",
        parse_mode="HTML",
    )
    return SEA_PAYMENT


async def sea_payment(update, c):
    value = update.message.text.strip().lower()
    if value in {"1", "تهران", "tehran", "iran"}:
        c.user_data["sea_payment_method"] = "tehran"
        await update.message.reply_text(
            "🇮🇷 <b>STEP 13/19 — Tehran Tax</b>\n\n"
            "درصد مالیات/هزینه تهران را وارد کنید.\n"
            "Enter Tehran tax/cost percentage.\n\n"
            "پیش‌فرض / Default: <b>3</b>",
            parse_mode="HTML",
        )
        return TEHRAN_TAX
    if value in {"2", "امارات", "uae", "dubai", "ابوظبی"}:
        c.user_data["sea_payment_method"] = "uae"
        await update.message.reply_text(
            "🇦🇪 <b>STEP 13/19 — USD/AED Rate</b>\n\n"
            "نرخ پرداخت USD/AED را وارد کنید.\n"
            "Enter USD/AED payment rate.\n\n"
            "پیش‌فرض / Default: <b>3.685</b>",
            parse_mode="HTML",
        )
        return UAE_AED_RATE
    await update.message.reply_text("❌ فقط 1 یا 2 را ارسال کنید. / Send 1 or 2.")
    return SEA_PAYMENT


async def tehran_tax(update, c):
    try:
        if to_decimal(update.message.text) < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ درصد نامعتبر است. / Invalid percentage.")
        return TEHRAN_TAX
    c.user_data["tehran_tax_pct"] = update.message.text.strip()
    await update.message.reply_text(
        "🧾 <b>STEP 14/19 — Switch Bill</b>\n\n"
        "هزینه Switch Bill به USD را وارد کنید؛ اگر ندارید 0 بزنید.\n"
        "Enter Switch Bill cost in USD; enter 0 if none.",
        parse_mode="HTML",
    )
    return SWITCH_BILL


async def uae_aed_rate(update, c):
    try:
        if to_decimal(update.message.text) <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ نرخ نامعتبر است. / Invalid rate.")
        return UAE_AED_RATE
    c.user_data["uae_aed_rate"] = update.message.text.strip()
    await update.message.reply_text(
        "🧾 <b>STEP 14/19 — Switch Bill</b>\n\n"
        "هزینه Switch Bill به USD را وارد کنید؛ اگر ندارید 0 بزنید.\n"
        "Enter Switch Bill cost in USD; enter 0 if none.",
        parse_mode="HTML",
    )
    return SWITCH_BILL


async def switch_bill(update, c):
    return await numeric_field(
        update, c, "switch_bill_usd",
        "📦 <b>STEP 15/19 — Cross Stuffing</b>\n\n"
        "هزینه Cross Stuffing به USD را وارد کنید؛ اگر ندارید 0 بزنید.\n"
        "Enter Cross Stuffing cost in USD; enter 0 if none.",
        CROSS_STUFFING,
    )


async def cross_stuffing(update, c):
    return await numeric_field(
        update, c, "cross_stuffing_usd",
        "💱 <b>STEP 16/19 — USD Exchange Rate</b>\n\n"
        "نرخ دلار به تومان را وارد کنید.\n"
        "Enter USD/IRR exchange rate.\n\n"
        "مثال / Example: <b>187000</b>",
        FX,
    )


async def fx(update, c):
    return await numeric_field(
        update, c, "fx",
        "📍 <b>STEP 17/19 — Destination</b>\n\n"
        "مقصد را وارد کنید.\nEnter destination.\n\n"
        "مثال / Example: <b>Nhava Sheva, India</b>",
        DESTINATION,
        minimum=Decimal("0.000001"),
    )


async def destination(update, c):
    return await text_field(
        update, c, "destination",
        "👤 <b>STEP 18/19 — Customer</b>\n\n"
        "نام مشتری را وارد کنید.\nEnter customer name.",
        CUSTOMER,
    )


async def customer_name(update, c):
    c.user_data["customer_name"] = update.message.text.strip()
    data = c.user_data.copy()
    try:
        result = calculate(data)
    except Exception:
        log.exception("Calculation failed")
        await update.message.reply_text(
            "❌ محاسبه انجام نشد. اطلاعات را بررسی کنید.\n"
            "Calculation failed. Please check the entered values."
        )
        return ConversationHandler.END

    c.user_data["last_result"] = result
    sea_label = "Tehran — USD + Tax" if result["sea_payment_method"] == "tehran" else "UAE — AED"
    sea_detail = (
        f"Tehran tax: {money(result['tehran_tax_pct'],2)}%"
        if result["sea_payment_method"] == "tehran"
        else f"USD/AED: {money(result['uae_aed_rate'],3)} | Payment: {money(result['sea_aed_amount'],2)} AED"
    )

    await update.message.reply_text(
        "✅ <b>CALCULATION COMPLETE | محاسبه انجام شد</b>\n\n"
        f"📦 Product: {data['product']}\n"
        f"📦 Packaging: {data['packaging']}\n"
        f"🔢 Packages: {money(to_decimal(data['packages']),0)}\n"
        f"⚖️ Gross Weight: {money(result['total_gross'],2)} KG\n"
        f"⚖️ Net Weight: {money(result['total_net'],2)} KG\n\n"
        f"🚢 Sea Freight: {sea_label}\n{sea_detail}\n\n"
        f"🔐 Landed Cost: {money(result['cost_usd_kg'],3)} USD/KG\n"
        f"💵 <b>Final Customer Price: {money(result['customer_price'],2)} USD/KG</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 Customer Quotation | PDF", callback_data="customer_offer")],
            [InlineKeyboardButton("🧮 محاسبه جدید | New Calculation", callback_data="new")],
            [InlineKeyboardButton("📋 Formula | فرمول", callback_data="formula")],
        ]),
    )
    return ConversationHandler.END


async def profile_start(update, c):
    ensure_user(update.effective_user)
    q = update.callback_query
    if q:
        await q.answer()
        msg = q.message
    else:
        msg = update.message
    c.user_data.clear()
    await msg.reply_text(
        "🏢 <b>Company Profile</b>\n\nنام شرکت را وارد کنید.\nEnter company name.",
        parse_mode="HTML",
    )
    return PROFILE_COMPANY


async def profile_company(update, c):
    c.user_data["profile_company"] = update.message.text.strip()
    await update.message.reply_text("📍 آدرس شرکت را به انگلیسی وارد کنید.\nEnter company address in English.")
    return PROFILE_ADDRESS


async def profile_address(update, c):
    c.user_data["profile_address"] = update.message.text.strip()
    await update.message.reply_text("📞 شماره تماس شرکت را وارد کنید.\nEnter company phone/WhatsApp.")
    return PROFILE_PHONE


async def profile_phone(update, c):
    c.user_data["profile_phone"] = update.message.text.strip()
    await update.message.reply_text("🖼 لوگوی شرکت را ارسال کنید یا SKIP بزنید.\nSend company logo or type SKIP.")
    return PROFILE_LOGO


async def profile_logo(update, c):
    logo = update.message.photo[-1].file_id if update.message.photo else None
    if not logo and (not update.message.text or update.message.text.strip().lower() not in {"skip","no","ندارم","خیر"}):
        await update.message.reply_text("لطفاً عکس لوگو یا SKIP ارسال کنید.")
        return PROFILE_LOGO
    save_profile(
        update.effective_user.id,
        c.user_data["profile_company"],
        c.user_data["profile_address"],
        c.user_data["profile_phone"],
        logo,
    )
    c.user_data.clear()
    await update.message.reply_text(
        "✅ Company Profile saved | پروفایل شرکت ذخیره شد.",
        reply_markup=main_keyboard(update.effective_user.id),
    )
    return ConversationHandler.END


def create_customer_pdf(data, result, profile, path, logo_path=None):
    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Title"], fontSize=18, leading=21, alignment=1, textColor=colors.white)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=13, alignment=1)
    big = ParagraphStyle("big", parent=styles["Title"], fontSize=27, leading=32, alignment=1)
    small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=8.5, leading=11)

    doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=30, bottomMargin=30)
    story = []

    cells = []
    if logo_path and os.path.exists(logo_path):
        from reportlab.platypus import Image as RLImage
        cells.append(RLImage(logo_path, width=62, height=62, kind="proportional"))
    cells.append(Paragraph("<b>EXPORT QUOTATION</b>", title))
    widths = [78, 442] if len(cells) == 2 else [520]
    header = Table([cells], colWidths=widths)
    header.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#17365D")),
        ("ALIGN",(0,0),(-1,-1),"CENTER"), ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),9), ("BOTTOMPADDING",(0,0),(-1,-1),9),
    ]))
    story += [header, Spacer(1,8)]

    company = Table([[
        Paragraph(
            f"<b>{profile['company_name']}</b><br/>{profile['address']}<br/>Mobile: {profile['phone']}",
            body
        )
    ]], colWidths=[520])
    company.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#D9EAF7")),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("TOPPADDING",(0,0),(-1,-1),7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
    ]))
    story += [company, Spacer(1,15)]

    rows = [
        ["Quotation No.", datetime.now().strftime("TTA-%Y%m%d-%H%M")],
        ["Date", datetime.now().strftime("%Y/%m/%d")],
        ["Customer", data.get("customer_name","-")],
        ["Product", data["product"]],
        ["Packaging", data["packaging"]],
        ["Packages", money(to_decimal(data["packages"]),0)],
        ["Gross Weight", f"{money(result['total_gross'],2)} KG"],
        ["Net Weight", f"{money(result['total_net'],2)} KG"],
        ["Destination", data["destination"]],
    ]
    table = Table(rows, colWidths=[170,350])
    table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),.5,colors.HexColor("#B7B7B7")),
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#D9EAF7")),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("FONTSIZE",(0,0),(-1,-1),9.5),
        ("TOPPADDING",(0,0),(-1,-1),8), ("BOTTOMPADDING",(0,0),(-1,-1),8),
    ]))
    story += [table, Spacer(1,20)]

    offer = Table([
        [Paragraph("FINAL OFFER PRICE", body)],
        [Paragraph(f"{money(result['customer_price'],2)} USD / KG", big)],
        [Paragraph(f"TOTAL SHIPMENT VALUE: {money(result['shipment_value'],2)} USD", body)],
    ], colWidths=[520])
    offer.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#E2F0D9")),
        ("BOX",(0,0),(-1,-1),.8,colors.HexColor("#70AD47")),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("TOPPADDING",(0,0),(-1,-1),10), ("BOTTOMPADDING",(0,0),(-1,-1),10),
    ]))
    story += [
        offer, Spacer(1,18),
        Paragraph("This quotation contains the final commercial offer only. Internal costs and logistics breakdown are excluded.", small)
    ]
    doc.build(story)


async def show_admin_panel(update, context):
    q = update.callback_query
    if q:
        await q.answer()
        msg = q.message
        uid = q.from_user.id
    else:
        msg = update.message
        uid = update.effective_user.id

    if not is_admin(uid):
        await msg.reply_text("⛔ Access denied | دسترسی غیرمجاز")
        return

    total, trials, active, unused, expired = admin_stats()
    await msg.reply_text(
        "👑 <b>T.T.A ADMIN PANEL</b>\n"
        "پنل مدیریت حرفه‌ای\n\n"
        f"👥 Users | کاربران: <b>{total}</b>\n"
        f"🎁 Active Trials | تست فعال: <b>{trials}</b>\n"
        f"🟢 Active Licenses | لایسنس فعال: <b>{active}</b>\n"
        f"🔑 Unused Licenses | استفاده‌نشده: <b>{unused}</b>\n"
        f"🔴 Expired Trials | تست منقضی: <b>{expired}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ 30 روز", callback_data="lic30"),
             InlineKeyboardButton("➕ 90 روز", callback_data="lic90")],
            [InlineKeyboardButton("➕ 1 سال", callback_data="lic365"),
             InlineKeyboardButton("♾ دائمی", callback_data="licperm")],
            [InlineKeyboardButton("📋 لایسنس‌ها | Licenses", callback_data="liclist")],
            [InlineKeyboardButton("👥 کاربران | Users", callback_data="userlist")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="home")],
        ]),
    )


async def admin_action(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if not is_admin(uid):
        await q.message.reply_text("⛔ Access denied.")
        return

    if q.data in {"lic30","lic90","lic365","licperm"}:
        days = {"lic30":30, "lic90":90, "lic365":365}.get(q.data)
        permanent = q.data == "licperm"
        key, exp = create_license(days, permanent)
        validity = "Permanent / دائمی" if permanent else f"{days} days"
        await q.message.reply_text(
            "✅ <b>LICENSE CREATED | لایسنس ساخته شد</b>\n\n"
            f"🔑 <code>{key}</code>\n"
            f"⏳ Validity: <b>{validity}</b>\n"
            "🟡 Status: UNUSED\n\n"
            "این کد را برای مشتری ارسال کنید.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("👑 Admin Panel", callback_data="admin")]]
            ),
        )
        return

    if q.data == "liclist":
        conn = db_connect()
        rows = conn.execute(
            "SELECT license_key,status,expires_at FROM licenses ORDER BY created_at DESC LIMIT 25"
        ).fetchall()
        conn.close()
        if rows:
            txt = "📋 <b>LICENSE LIST</b>\n\n" + "\n".join(
                f"<code>{r['license_key']}</code> — {r['status']} — {r['expires_at'] or 'PERMANENT'}"
                for r in rows
            )
        else:
            txt = "📋 هنوز لایسنسی ساخته نشده است."
        await q.message.reply_text(
            txt, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("👑 Admin Panel", callback_data="admin")]]
            ),
        )
        return

    if q.data == "userlist":
        conn = db_connect()
        rows = conn.execute(
            "SELECT user_id,username,status,trial_end,license_key FROM users ORDER BY last_seen DESC LIMIT 25"
        ).fetchall()
        conn.close()
        if rows:
            txt = "👥 <b>RECENT USERS | کاربران اخیر</b>\n\n" + "\n".join(
                f"<code>{r['user_id']}</code> | @{r['username'] or '-'} | {r['status']} | {r['license_key'] or '-'}"
                for r in rows
            )
        else:
            txt = "👥 No users yet."
        await q.message.reply_text(
            txt, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("👑 Admin Panel", callback_data="admin")]]
            ),
        )


async def callback(update, context):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "home":
        await q.message.reply_text(
            "🌿 <b>T.T.A EXPORT CALCULATOR</b>\n\n" + access_message(q.from_user.id),
            parse_mode="HTML",
            reply_markup=main_keyboard(q.from_user.id),
        )
    elif data == "license":
        await license_menu(update, context)
    elif data == "enter_license":
        await enter_license_prompt(update, context)
    elif data == "contact":
        await creator_contact(update, context)
    elif data == "help":
        await help_menu(update, context)
    elif data == "admin":
        await show_admin_panel(update, context)
    elif data == "formula":
        await q.message.reply_text(
            "🧮 <b>Formula | فرمول</b>\n\n"
            "Origin = Product + Packaging/Labor + Profit\n"
            "Gross Weight = Packages × Gross Weight/Package\n"
            "Customer Price = Landed Cost rounded UP to $0.05",
            parse_mode="HTML",
        )
    elif data == "profile":
        await q.message.reply_text(
            "برای تکمیل پروفایل از /profile استفاده کنید.\n"
            "Use /profile to complete your company profile."
        )
    elif data == "customer_offer":
        values = context.user_data
        result = values.get("last_result")
        profile = get_profile(q.from_user.id)
        if not result or not profile:
            await q.message.reply_text("ابتدا محاسبه و پروفایل را کامل کنید.")
            return

        await q.message.reply_text(
            f"📄 <b>EXPORT QUOTATION</b>\n\n"
            f"Customer: {values.get('customer_name','-')}\n"
            f"Product: {values['product']}\n"
            f"Packaging: {values['packaging']}\n"
            f"Packages: {money(to_decimal(values['packages']),0)}\n"
            f"Gross Weight: {money(result['total_gross'],2)} KG\n"
            f"Net Weight: {money(result['total_net'],2)} KG\n"
            f"Destination: {values['destination']}\n\n"
            f"<b>FINAL OFFER PRICE: {money(result['customer_price'],2)} USD/KG</b>\n"
            f"TOTAL SHIPMENT VALUE: {money(result['shipment_value'],2)} USD\n\n"
            f"{profile['company_name']}\n{profile['address']}\nMobile: {profile['phone']}",
            parse_mode="HTML",
        )

        logo_path = None
        if profile.get("logo_file_id"):
            try:
                file = await context.bot.get_file(profile["logo_file_id"])
                logo_path = f"/tmp/tta_logo_{q.from_user.id}.png"
                await file.download_to_drive(logo_path)
            except Exception:
                log.exception("Logo download failed")

        pdf_path = f"/tmp/TTA_Customer_Quotation_{q.from_user.id}.pdf"
        create_customer_pdf(values, result, profile, pdf_path, logo_path)
        with open(pdf_path, "rb") as fh:
            await q.message.reply_document(
                fh, filename="TTA_Export_Quotation.pdf", caption="📄 Customer Quotation"
            )
        for path in (pdf_path, logo_path):
            if path:
                try:
                    os.remove(path)
                except OSError:
                    pass


async def cancel(update, context):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ عملیات لغو شد | Cancelled.",
        reply_markup=main_keyboard(update.effective_user.id),
    )
    return ConversationHandler.END


async def route_text(update, context):
    if await handle_license_text(update, context):
        return


async def myid(update, context):
    ensure_user(update.effective_user)
    await update.message.reply_text(f"🆔 Telegram User ID: {update.effective_user.id}")


async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("start", "شروع / Main menu"),
        BotCommand("new", "محاسبه جدید / New calculation"),
        BotCommand("profile", "پروفایل شرکت / Company profile"),
        BotCommand("license", "لایسنس / License"),
        BotCommand("admin", "پنل مدیریت / Admin panel"),
        BotCommand("contact", "ارتباط / Contact"),
        BotCommand("help", "راهنما / Help"),
        BotCommand("myid", "شناسه تلگرام / Telegram ID"),
        BotCommand("cancel", "لغو / Cancel"),
    ])


def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")

    db_connect().close()
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    profile_conv = ConversationHandler(
        entry_points=[
            CommandHandler("profile", profile_start),
            CallbackQueryHandler(profile_start, pattern=r"^profile$"),
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
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    calc_conv = ConversationHandler(
        entry_points=[
            CommandHandler("new", begin),
            CallbackQueryHandler(begin, pattern=r"^new$"),
        ],
        states={
            PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, product)],
            PACKAGING: [MessageHandler(filters.TEXT & ~filters.COMMAND, packaging)],
            PACKAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, packages)],
            GROSS_KG: [MessageHandler(filters.TEXT & ~filters.COMMAND, gross)],
            NET_KG: [MessageHandler(filters.TEXT & ~filters.COMMAND, net)],
            PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_price)],
            PACK_LABOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, pack_labor)],
            PROFIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, profit)],
            LAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, land)],
            CLEARANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, clearance)],
            SEA: [MessageHandler(filters.TEXT & ~filters.COMMAND, sea)],
            SEA_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, sea_payment)],
            TEHRAN_TAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, tehran_tax)],
            UAE_AED_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, uae_aed_rate)],
            SWITCH_BILL: [MessageHandler(filters.TEXT & ~filters.COMMAND, switch_bill)],
            CROSS_STUFFING: [MessageHandler(filters.TEXT & ~filters.COMMAND, cross_stuffing)],
            FX: [MessageHandler(filters.TEXT & ~filters.COMMAND, fx)],
            DESTINATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, destination)],
            CUSTOMER: [MessageHandler(filters.TEXT & ~filters.COMMAND, customer_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("contact", creator_contact))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("license", license_command))
    app.add_handler(CommandHandler("admin", show_admin_panel))
    app.add_handler(profile_conv)
    app.add_handler(calc_conv)
    app.add_handler(CallbackQueryHandler(admin_action, pattern=r"^(lic30|lic90|lic365|licperm|liclist|userlist)$"))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_text))

    log.info("TTA Export Calculator v%s started", VERSION)
    app.run_polling()


if __name__ == "__main__":
    main()
