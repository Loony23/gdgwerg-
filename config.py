#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Конфигурационный файл для Telegram-бота.
Загружает переменные окружения из .env файла.
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Внешние API
AMOCRM_API_KEY = os.getenv("AMOCRM_API_KEY")
AMOCRM_DOMAIN = os.getenv("AMOCRM_DOMAIN")
MIS_RENOVATIO_API_KEY = os.getenv("RENOVATIO_API_KEY")

# База данных PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "medical_bot_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Ключ шифрования для pgcrypto
PGP_KEY = os.getenv("PGP_KEY", "your_strong_encryption_key_here")
