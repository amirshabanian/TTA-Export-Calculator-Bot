# 🌿 T.T.A İhracat Maliyet Hesaplama Botu

**İhracat maliyetini hesaplayan ve müşteriye sunulabilir PDF teklif hazırlayan Telegram botu**

[English](README.md) · [فارسی](README.fa.md) · [简体中文](README.zh-CN.md) · [Русский](README.ru.md) · [Türkçe](README.tr.md)

## Proje hakkında

T.T.A Export Cost Calculator; paketleme, iç nakliye, gümrük ve deniz navlunu gibi giderleri tahmin etmeye ve müşteriye yönelik PDF teklif oluşturmaya yardımcı olur. Proje, **Shabanian Trading** kurucusu ve **Tamana Tejarat Armaghan (T.T.A)** iş ortağı **Amir Shabanian** tarafından sürdürülür.

## Özellikler

- Farsça/İngilizce bot akışı (mevcut konuşma akışına bağlıdır)
- Ürün, ambalaj, adet, net ve brüt ağırlık bilgileri
- Paketleme, işçilik, kara nakliyesi, gümrük ve deniz navlunu giderleri
- Navlun ödeme yöntemi ve döviz kuru girişleri
- Maliyet hesabı ve müşteriye yönelik PDF teklif
- SQLite tabanlı kullanıcı/lisans verileri
- Yönetici paneli, deneme süresi ve lisans yönetimi
- Ubuntu VPS için systemd şablonu ve veritabanı yedekleme betiği

## Hızlı başlangıç

Python 3.10+ ve [BotFather](https://t.me/BotFather) üzerinden oluşturulmuş bir bot token'ı gerekir.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

`TELEGRAM_BOT_TOKEN`, `TTA_ADMIN_IDS` ve kalıcı depolama üzerindeki `TTA_DB_PATH` değişkenlerini ayarlayın. Gerçek token'ı veya `.env` dosyasını GitHub'a yüklemeyin.

## Dağıtım ve güncelleme

Railway kalıcı Volume kurulumu, Ubuntu VPS systemd servisi ve güvenli güncelleme için [DEPLOYMENT.md](DEPLOYMENT.md) dosyasına bakın. Aynı bot token'ı için yalnızca bir long-polling örneği çalıştırılmalıdır; Railway ve VPS'yi aynı anda çalıştırmayın.

## Güvenlik

Token, veritabanı, log veya müşteri belgelerini depoya eklemeyin. Güncellemeden önce SQLite yedeği alın. Dağıtımdan sonra `/start`, yönetici paneli, tam hesaplama akışı ve PDF üretimini test edin.

- Telegram: [@tamana_tejarat](https://t.me/tamana_tejarat)
- WhatsApp: [İletişim](https://wa.me/qr/DDNAEFASNGBAP1)

Not: Dil bağlantıları ayrı README dosyalarını açar; GitHub arayüz dilini değiştirmek README içeriğini otomatik olarak çevirmez.
