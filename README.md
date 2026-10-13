# T.T.A Export Calculator — Stable 6.1.0

**محاسبه‌گر صادرات T.T.A — نسخه پایدار ۶.۱.۰**  
Developed by **Amir Shabanian** · Shabanian Trading / بازرگانی شعبانیان · Tamana Tejarat Armaghan (T.T.A) / تمنا تجارت ارمغان

## فارسی

ربات تلگرام دوزبانه برای محاسبه بهای تمام‌شده صادرات و ساخت پیش‌فاکتور PDF مشتری.

### امکانات نسخه ۶.۱.۰
- رابط و راهنمای فارسی/انگلیسی.
- محاسبه بر اساس **وزن ناخالص**؛ وزن خالص نیز برای اطلاعات و پیش‌فاکتور ثبت می‌شود.
- محاسبه هزینه محصول، بسته‌بندی/کار، سود، حمل داخلی، ترخیص، حمل دریایی، Switch Bill و Cross Stuffing.
- روش پرداخت حمل دریایی تهران (با درصد مالیات قابل تنظیم) یا امارات (نمایش معادل پرداخت AED با نرخ USD/AED).
- گرد کردن قیمت نهایی مشتری رو به بالا با گام ۰٫۰۵ دلار به‌ازای هر کیلو.
- پروفایل شرکت، لوگو و PDF مشتری؛ PDF فقط قیمت نهایی و مشخصات تجاری را نمایش می‌دهد و ریز هزینه‌ها/سود داخلی را افشا نمی‌کند.
- آزمایشی ۷ روزه، لایسنس کاربرمحور و پنل مدیریت.
- پذیرش اعداد فارسی/عربی در فیلدهای عددی، اعتبارسنجی ورودی، پیام خطای قابل‌فهم برای ورودی غیرمتنی.
- امکان خروج از مراحل با `/cancel`؛ فرمان‌های منو در جریان مکالمه باعث گیرکردن دائمی مراحل نمی‌شوند.
- SQLite با timeout و busy timeout برای کاهش خطاهای قفل دیتابیس.

### استقرار صحیح در Railway (مهم)
1. محتوای ZIP را در ریشه مخزن GitHub قرار بده؛ `bot.py`, `requirements.txt`, `README.md`, `railway.json`, `Procfile`, `.gitignore` و `.env.example` باید در ریشه باشند.
2. در Railway → Variables متغیر `TELEGRAM_BOT_TOKEN` را با توکن واقعی تنظیم کن. توکن را داخل GitHub یا پیام‌ها قرار نده.
3. `TTA_ADMIN_IDS=5044844036` را تنظیم کن. چند شناسه را با کاما جدا کن.
4. در Railway یک **Volume** به مسیر `/data` وصل کن و سپس `TTA_DB_PATH=/data/tta_bot.db` را تنظیم کن. این مرحله برای ماندگاری پروفایل، لایسنس و کاربران ضروری است.
5. اگر قبلاً پروفایل/لایسنس ذخیره کرده‌ای، **قبل از تغییر `TTA_DB_PATH` از دیتابیس قبلی نسخه پشتیبان بگیر و آن را منتقل کن**؛ مسیر دیتابیس جدید و خالی شبیه پاک شدن پروفایل به نظر می‌رسد.
6. فقط **یک سرویس/Replica فعال** با این توکن اجرا کن. اجرای هم‌زمان چند نسخه باعث خطای Telegram `Conflict: terminated by other getUpdates request` می‌شود.
7. Deploy جدید را انجام بده و در Logs تأیید کن پیام `TTA Export Calculator v6.1.0 started` و مسیر درست دیتابیس دیده می‌شود.

### تست پس از استقرار
- `/start` باید Version 6.1.0 نشان دهد.
- پروفایل شرکت را ذخیره کن؛ بعد از Restart سرویس، وجود پروفایل را بررسی کن.
- محاسبه آزمایشی را از محصول تا نام مشتری کامل کن و PDF مشتری بگیر.
- در یک مرحله `/cancel` بزن و سپس یک محاسبه جدید شروع کن.
- اعداد فارسی مثل `۱۲۳۴۵` را در یک ورودی عددی آزمایش کن.

### نکته شفافیت
این بسته با بررسی نحوی Python و تست‌های محاسباتی محلی آماده شده است؛ امکان آزمایش زنده با توکن تلگرام یا محیط Railway شما از اینجا وجود ندارد. بنابراین پس از Deploy، تست‌های بالا ضروری‌اند. پایداری اطلاعات روی Railway به تنظیم صحیح Volume وابسته است.

## English

A bilingual Telegram bot for export landed-cost calculations and customer-ready PDF quotations.

### Deployment checklist
- Keep all package files at the repository root.
- Set `TELEGRAM_BOT_TOKEN` and `TTA_ADMIN_IDS` in Railway Variables only.
- Attach a Railway Volume at `/data`, then set `TTA_DB_PATH=/data/tta_bot.db`.
- Back up/migrate the old SQLite database before changing its path.
- Run exactly one active polling instance for this bot token.
- After deployment, verify version 6.1.0, profile persistence after restart, a complete calculation, PDF output, and `/cancel` recovery.

### Environment variables
See `.env.example`. Never commit a real bot token or a database file.
