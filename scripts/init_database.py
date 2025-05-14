#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для инициализации базы данных PostgreSQL.
"""

import sys
import os
import logging
import traceback

# Добавление корневой директории проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.database import engine, Base
from db.models import Patient, Service, Notification, WebhookEvent, Conversation
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def init_database():
    """
    Инициализация базы данных PostgreSQL.
    Создает расширение pgcrypto и все необходимые таблицы.
    """
    try:
        # Вывод информации о подключении (без пароля)
        logger.info(f"Подключение к базе данных: {DB_HOST}:{DB_PORT}/{DB_NAME} (пользователь: {DB_USER})")
        
        # Создание соединения
        conn = engine.connect()
        logger.info("Соединение с базой данных установлено")
        
        # Создание расширения pgcrypto для шифрования
        logger.info("Создание расширения pgcrypto...")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))
        conn.commit()
        logger.info("Расширение pgcrypto создано или уже существует")
        
        # Создание таблиц
        logger.info("Создание таблиц...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("База данных PostgreSQL успешно инициализирована")
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        logger.error(traceback.format_exc())  # Вывод полного стека ошибки
        return False

if __name__ == "__main__":
    print("Инициализация базы данных PostgreSQL")
    success = init_database()
    
    if success:
        print("База данных успешно инициализирована")
    else:
        print("Ошибка при инициализации базы данных. Проверьте логи для получения дополнительной информации.")
