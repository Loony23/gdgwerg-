#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Основной файл запуска Telegram-бота для медицинской клиники.
"""

import logging
from telegram.ext import Application

from config import TELEGRAM_BOT_TOKEN
from bot.core.setup import setup_bot
from db.database import init_db

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Запуск бота"""
    logger.info("Инициализация базы данных PostgreSQL...")
    init_db()
    
    logger.info("Запуск бота...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Настройка бота (регистрация обработчиков и т.д.)
    setup_bot(application)
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
