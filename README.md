# T.T.A Export Calculator | محاسبه‌گر صادرات T.T.A

**نسخه جاری / Current version: 6.0.5**  
**Developed by Amir Shabanian | توسعه‌دهنده: امیر شعبانیان**  
Shabanian Trading | بازرگانی شعبانیان  
Tamana Tejarat Armaghan (T.T.A) | تمنا تجارت ارمغان

---

## فارسی

ربات تلگرام محاسبه قیمت تمام‌شده صادرات، محاسبه قیمت پیشنهادی مشتری و تولید پیش‌فاکتور PDF.

### امکانات
- رابط و راهنمای دوزبانه فارسی و انگلیسی
- محاسبه هزینه محصول، بسته‌بندی و نیروی کار، سود، حمل داخلی، ترخیص و حمل دریایی
- انتخاب روش پرداخت حمل دریایی: تهران با مالیات قابل تنظیم یا امارات با نرخ USD/AED
- هزینه‌های Switch Bill و Cross Stuffing
- محاسبه قیمت نهایی بر مبنای وزن ناخالص و گرد کردن رو به بالا با گام ۰٫۰۵ دلار به‌ازای هر کیلو
- پروفایل شرکت و درج اطلاعات شرکت در پیش‌فاکتور مشتری
- خروجی PDF مشتری بدون نمایش جزئیات محرمانه هزینه‌های داخلی
- دوره آزمایشی، لایسنس و پنل مدیریت

### نصب و استقرار در Railway
1. فایل `bot.py` و `requirements.txt` را در مخزن قرار دهید.
2. متغیر محیطی `TELEGRAM_BOT_TOKEN` را در Railway تنظیم کنید؛ توکن را در GitHub قرار ندهید.
3. شناسه مدیر را در `TTA_ADMIN_IDS` تنظیم کنید.
4. برای حفظ پروفایل‌ها و لایسنس‌ها، یک Railway Volume به مسیر `/data` متصل و متغیر `TTA_DB_PATH=/data/tta_bot.db` را تنظیم کنید. پیش از تغییر مسیر دیتابیس، از فایل دیتابیس فعلی نسخه پشتیبان بگیرید و در صورت وجود داده‌های قبلی، آن‌ها را منتقل کنید.
5. فقط **یک نمونه فعال** از ربات را با همین توکن اجرا کنید؛ اجرای هم‌زمان چند نمونه می‌تواند خطای `Conflict: terminated by other getUpdates request` ایجاد کند.
6. پس از Deploy، یک محاسبه کامل را تا دریافت PDF آزمایش کنید.

### نکته پایداری
اطلاعات پروفایل در SQLite ذخیره می‌شود. اگر فایل دیتابیس روی فضای موقت سرویس باشد، ممکن است پس از استقرار مجدد از دسترس خارج شود. برای جلوگیری از این مشکل، Volume پایدار را تنظیم کنید و در لاگ شروع برنامه مسیر دیتابیس را بررسی کنید.

---

## English

A bilingual Telegram bot for export landed-cost calculation and customer-ready PDF quotations.

### Features
- Persian and English prompts and menus
- Product, packaging/labor, profit, inland transport, customs clearance, and sea freight calculations
- Tehran freight payment with configurable tax, or UAE payment using a USD/AED rate
- Switch Bill and Cross Stuffing charges
- Customer price calculated per gross kilogram and rounded upward to the next USD 0.05
- Company profile stored in SQLite and used in customer quotations
- Customer-facing PDF excludes internal cost breakdowns
- Trial, license, and administrator workflows

### Railway deployment
1. Commit `bot.py` and `requirements.txt` to the repository.
2. Set `TELEGRAM_BOT_TOKEN` in Railway Variables. Never commit the token to GitHub.
3. Set `TTA_ADMIN_IDS` to the authorized Telegram user ID(s).
4. Attach a persistent Railway Volume at `/data` and set `TTA_DB_PATH=/data/tta_bot.db` to retain profiles and license data. Back up and migrate any existing database before changing its path.
5. Run exactly **one active polling instance** per bot token to avoid Telegram polling conflicts.
6. After deployment, test the complete calculation flow and PDF generation.

### Support / ارتباط
- **Amir Shabanian**
- **Shabanian Trading | بازرگانی شعبانیان**
- **Tamana Tejarat Armaghan (T.T.A) | تمنا تجارت ارمغان**
- Telegram: [@tamana_tejarat](https://t.me/tamana_tejarat)
- WhatsApp: [Contact](https://wa.me/qr/DDNAEFASNGBAP1)
