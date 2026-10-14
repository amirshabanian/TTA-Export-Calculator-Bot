# 🌿 T.T.A 出口成本计算 Telegram 机器人

**用于估算出口到岸成本并生成客户报价 PDF 的 Telegram 机器人**

[English](README.md) · [فارسی](README.fa.md) · [简体中文](README.zh-CN.md) · [Русский](README.ru.md) · [Türkçe](README.tr.md)

## 简介

T.T.A 出口成本计算器帮助出口商估算运输、包装、清关和海运等成本，并生成面向客户的报价 PDF。项目由 **Amir Shabanian** 维护，他是 **Shabanian Trading** 创始人及 **Tamana Tejarat Armaghan (T.T.A)** 商业合作伙伴。

## 功能

- 波斯语/英语交互流程（取决于机器人当前流程）
- 产品、包装、数量、净重和毛重录入
- 包装、人工、内陆运输、海关及海运成本录入
- 运费支付方式和汇率录入
- 到岸成本计算和客户报价 PDF
- SQLite 用户和许可证数据
- 管理面板、试用期和许可证管理
- Ubuntu systemd 服务模板和数据库备份脚本

## 快速开始

需要 Python 3.10+ 和通过 [BotFather](https://t.me/BotFather) 创建的机器人令牌。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

请在本地或托管平台的环境变量中设置 `TELEGRAM_BOT_TOKEN`、`TTA_ADMIN_IDS` 和持久化存储中的 `TTA_DB_PATH`。不要将真实令牌或 `.env` 上传到 GitHub。

## 部署

请参阅 [DEPLOYMENT.md](DEPLOYMENT.md)，了解 Railway 持久化卷、Ubuntu VPS 的 systemd 部署以及安全更新流程。每个机器人令牌只能运行一个长轮询实例；不要同时运行 Railway 和 VPS 实例。

## 安全提示

不要提交令牌、数据库、日志、客户文件或私钥。更新前备份 SQLite 数据库。部署后请测试 `/start`、管理面板、完整计算流程和 PDF 生成。

- Telegram 支持：[ @tamana_tejarat](https://t.me/tamana_tejarat)
- WhatsApp：[联系](https://wa.me/qr/DDNAEFASNGBAP1)

注意：顶部语言链接打开各自的 README 文件。GitHub 界面语言切换不会自动翻译 README。
