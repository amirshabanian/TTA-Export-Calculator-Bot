# بسته استقرار رایگان بلندمدت T.T.A — نسخه 6.2.0 Oracle

این بسته برای انتقال ربات Python/Telegram از Railway به یک ماشین مجازی Ubuntu در Oracle Cloud Free Tier تهیه شده است. **رایگان‌بودن و فعال‌شدن حساب Oracle تضمین‌شده نیست**؛ Oracle ممکن است به‌دلیل کشور/منطقه، ظرفیت یا بررسی حساب، ثبت‌نام یا ساخت ماشین مجازی را نپذیرد. قبل از مهاجرت نهایی، سرور و اتصال تلگرام را آزمایش کنید.

## داخل بسته
- `bot.py`: کد ربات (بر پایه نسخه موجود 6.1.0؛ نسخه بسته 6.2.0-ORACLE)
- `requirements.txt`: وابستگی‌های Python
- `tta-bot.service`: اجرای خودکار و راه‌اندازی مجدد پس از Crash/Reboot
- `scripts/install_ubuntu.sh`: نصب وابستگی‌ها و آماده‌سازی سرویس
- `scripts/backup_db.sh`: پشتیبان‌گیری سازگار از SQLite
- `test_calculations.py`: تست‌های پایه محاسبات
- `.env.example`: الگوی تنظیمات محرمانه

## مرحله 1 — ساخت سرور Oracle
1. به https://www.oracle.com/cloud/free/ برو و حساب بساز. ممکن است برای تأیید حساب به کارت پرداخت و شماره تلفن نیاز باشد؛ شرایط در کشورها متفاوت است.
2. از بخش Compute یک VM رایگان سازگار با Always Free بساز (معمولاً Ampere A1 یا شکل‌های مجاز Free Tier؛ موجودی و شرایط را در پنل خود بررسی کن).
3. سیستم‌عامل Ubuntu LTS انتخاب کن و کلید SSH را دانلود/ذخیره کن. کلید خصوصی را با کسی به اشتراک نگذار.
4. در شبکه ماشین، دسترسی SSH روی پورت 22 را فقط از IP خودت باز کن. برای ربات تلگرام نیازی به بازکردن پورت ورودی عمومی دیگری نیست؛ ارتباط Telegram از سمت سرور به اینترنت برقرار می‌شود.
5. اگر ساخت VM شکست خورد، بعداً دوباره تلاش کن یا Region/shape مجاز دیگری را طبق ظرفیت حساب بررسی کن. هیچ راهی برای تضمین ظرفیت رایگان وجود ندارد.

## مرحله 2 — اتصال به سرور
از Termius در اندروید یا SSH روی کامپیوتر وصل شو. آدرس IP عمومی، نام کاربری (اغلب `ubuntu`) و کلید SSH را از Oracle بردار. سپس بسته ZIP را به سرور منتقل کن (SFTP در Termius یا `scp`).

روی سرور اجرا کن:

```bash
sudo apt-get update
sudo apt-get install -y unzip
mkdir -p ~/tta-package
unzip TTA_FreeHost_Oracle_Package.zip -d ~/tta-package
cd ~/tta-package
sudo bash scripts/install_ubuntu.sh
```

نام ZIP را مطابق فایلی که واقعاً منتقل کرده‌ای وارد کن. اگر فایل در پوشه دیگری است، مسیر واقعی را بنویس.

## مرحله 3 — توکن و تنظیمات

```bash
sudo nano /opt/tta-bot/.env
```

مقدار `TELEGRAM_BOT_TOKEN` را با توکن BotFather جایگزین کن. شناسه مدیر در `TTA_ADMIN_IDS` باید Telegram numeric ID خودت باشد. توکن را در GitHub، عکس، پیام یا چت قرار نده. ذخیره در nano: `Ctrl+O` سپس Enter؛ خروج: `Ctrl+X`.

در این بسته دیتابیس روی `/var/lib/tta-bot/tta_bot.db` نگهداری می‌شود. این مسیر روی دیسک VM است و با Restart سرویس باقی می‌ماند؛ اما خرابی/حذف VM می‌تواند اطلاعات را از بین ببرد، پس بکاپ خارج از VM هم داشته باش.

## مرحله 4 — اجرای سرویس

```bash
sudo systemctl enable --now tta-bot
sudo systemctl status tta-bot --no-pager
sudo journalctl -u tta-bot -n 100 --no-pager
```

مشاهده زنده گزارش‌ها:

```bash
sudo journalctl -u tta-bot -f
```

راه‌اندازی مجدد:

```bash
sudo systemctl restart tta-bot
```

توقف:

```bash
sudo systemctl stop tta-bot
```

`Restart=always` باعث می‌شود systemd بعد از Crash یا راه‌اندازی مجدد سرور، ربات را دوباره اجرا کند. این قابلیت خطای منطقی داخل کد را خودبه‌خود رفع نمی‌کند؛ خطاها باید از Logs تشخیص داده شوند.

## مرحله 5 — بکاپ روزانه دیتابیس

```bash
sudo bash /opt/tta-bot/scripts/backup_db.sh
```

برای بکاپ روزانه ساعت 03:15 UTC:

```bash
sudo crontab -e
```

این خط را اضافه کن:

```cron
15 3 * * * /bin/bash /opt/tta-bot/scripts/backup_db.sh >> /var/log/tta-bot-backup.log 2>&1
```

بکاپ روی همان VM است؛ هر چند وقت یک‌بار فایل‌های پوشه `/var/lib/tta-bot/backups` را با SFTP به دستگاه امن دیگری منتقل کن.

## مرحله 6 — مهاجرت دیتابیس قبلی Railway (اختیاری، اما مهم)
اگر کاربران، پروفایل شرکت، لایسنس‌ها یا سوابق قبلی مهم‌اند، قبل از قطع Railway از دیتابیس فعلی نسخه پشتیبان بگیر. مسیر دیتابیس را در Logs یا `TTA_DB_PATH` بررسی کن. اگر Railway Volume دارد، سرویس را متوقف کن و فایل SQLite و فایل‌های همراه `-wal`/`-shm` را با روش امن منتقل کن؛ ترجیحاً از SQLite backup API استفاده شود. دیتابیس جدید را بدون بکاپ روی دیتابیس قبلی کپی نکن. پس از انتقال، مالکیت فایل باید برای کاربر `tta-bot` تنظیم شود:

```bash
sudo chown tta-bot:tta-bot /var/lib/tta-bot/tta_bot.db
sudo chmod 0640 /var/lib/tta-bot/tta_bot.db
sudo systemctl restart tta-bot
```

اگر مسیر قبلی مشخص نیست یا دیتابیس در Railway ephemeral بوده، ممکن است لازم شود از پروفایل و تنظیمات دوباره نسخه‌برداری کنی.

## مرحله 7 — آزمایش نهایی
1. در تلگرام `/start` بزن و نسخه `6.2.0-ORACLE` را بررسی کن.
2. Company Profile را ذخیره کن و ربات را Restart کن؛ پروفایل باید باقی بماند.
3. یک محاسبه آزمایشی را تا انتها انجام بده و PDF مشتری را باز کن.
4. `/cancel` و `/start` را آزمایش کن.
5. با `sudo journalctl -u tta-bot -f` مطمئن شو خطای مکرر یا `Conflict: terminated by other getUpdates request` وجود ندارد.

**مهم:** پس از فعال‌شدن نسخه Oracle، نمونه Railway را متوقف کن تا هر دو نمونه هم‌زمان از یک توکن استفاده نکنند. قبل از توقف Railway مطمئن شو نسخه جدید و دیتابیس موردنیاز درست کار می‌کنند.

## نکته درباره دوره آزمایشی داخل خود ربات
میزبانی رایگان Oracle با Trial نرم‌افزاری ربات فرق دارد. مقدار `TTA_TRIAL_DAYS=7` دوره آزمایشی کاربران داخل منطق لایسنس ربات را تعیین می‌کند؛ برای مدیر تعریف‌شده در `TTA_ADMIN_IDS` دسترسی مدیر در نظر گرفته شده است. این متغیر را با هزینه هاست اشتباه نگیر.

## English quick notes
- Ubuntu VM + `systemd` keeps the bot running and restarts it after process failures/reboots.
- Configure secrets only in `/opt/tta-bot/.env`.
- Database: `/var/lib/tta-bot/tta_bot.db`.
- Logs: `sudo journalctl -u tta-bot -f`.
- Free-tier eligibility/capacity is not guaranteed. Keep off-host backups and stop the old Railway poller only after verifying the new deployment.
