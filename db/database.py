#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для работы с базой данных PostgreSQL.
"""

import logging
import urllib.parse
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, PGP_KEY

# Настройка логирования
logger = logging.getLogger(__name__)

# Создание базового класса для моделей
Base = declarative_base()

# Безопасное формирование строки подключения с экранированием специальных символов
password = urllib.parse.quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создание движка SQLAlchemy с явным указанием кодировки
engine = create_engine(
    DATABASE_URL,
    client_encoding='utf8',
    connect_args={
        'client_encoding': 'utf8'
    }
)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Функция-генератор для получения сессии базы данных.
    Гарантирует закрытие сессии после использования.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Инициализация базы данных.
    Создает расширение pgcrypto, если оно не существует.
    """
    try:
        # Создание соединения
        conn = engine.connect()
        
        # Создание расширения pgcrypto для шифрования
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))
        conn.commit()
        
        # Импорт моделей для создания таблиц
        from db.models import Patient, Service, Notification, WebhookEvent, Conversation
        
        # Создание таблиц
        Base.metadata.create_all(bind=engine)
        
        logger.info("База данных успешно инициализирована")
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise

def encrypt_text(text_value):
    """
    Функция для шифрования текстовых данных с помощью pgcrypto.
    
    Args:
        text_value: Текст для шифрования
        
    Returns:
        SQLAlchemy выражение для шифрования
    """
    if text_value is None:
        return None
    return text(f"pgp_sym_encrypt(:text_value, :key)").bindparams(text_value=text_value, key=PGP_KEY)

def decrypt_text(encrypted_value):
    """
    Функция для расшифровки данных с помощью pgcrypto.
    
    Args:
        encrypted_value: Зашифрованное значение
        
    Returns:
        SQLAlchemy выражение для расшифровки
    """
    if encrypted_value is None:
        return None
    return text(f"pgp_sym_decrypt(:encrypted_value::bytea, :key)").bindparams(encrypted_value=encrypted_value, key=PGP_KEY)
