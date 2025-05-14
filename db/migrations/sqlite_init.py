#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для инициализации зашифрованной базы данных SQLite.
Создает все необходимые таблицы.
"""

import os
import sys
import logging

# Добавление корневой директории проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db.database import engine
from db.models import Base

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def create_tables():
    """
    Создание всех таблиц в зашифрованной базе данных.
    """
    try:
        logger.info("Создание таблиц в зашифрованной базе данных SQLite...")
        Base.metadata.create_all(bind=engine)
        logger.info("Таблицы успешно созданы")
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}")
        raise

if __name__ == "__main__":
    create_tables()
