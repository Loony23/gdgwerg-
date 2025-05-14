#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Сервис для работы с пользователями в базе данных.
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db.models import User

logger = logging.getLogger(__name__)

def get_user_by_telegram_id(db: Session, telegram_id: int) -> User:
    """
    Получение пользователя по Telegram ID.
    
    Args:
        db: Сессия базы данных
        telegram_id: ID пользователя в Telegram
        
    Returns:
        User: Объект пользователя или None, если пользователь не найден
    """
    try:
        return db.query(User).filter(User.telegram_id == telegram_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при получении пользователя: {e}")
        return None

def get_or_create_user(db: Session, telegram_id: int) -> User:
    """
    Получение существующего пользователя или создание нового.
    
    Args:
        db: Сессия базы данных
        telegram_id: ID пользователя в Telegram
        
    Returns:
        User: Объект пользователя
    """
    user = get_user_by_telegram_id(db, telegram_id)
    
    if not user:
        # Создание нового пользователя
        now = datetime.utcnow()
        user = User(
            telegram_id=telegram_id,
            registration_date=now,
            last_activity=now,
            bot_state="new"
        )
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Создан новый пользователь с telegram_id={telegram_id}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Ошибка при создании пользователя: {e}")
            raise
    
    return user

def update_user_profile(db: Session, telegram_id: int, **kwargs) -> User:
    """
    Обновление профиля пользователя.
    
    Args:
        db: Сессия базы данных
        telegram_id: ID пользователя в Telegram
        **kwargs: Поля для обновления (phone_number, first_name, и т.д.)
        
    Returns:
        User: Обновленный объект пользователя
    """
    user = get_user_by_telegram_id(db, telegram_id)
    
    if not user:
        logger.error(f"Пользователь с telegram_id={telegram_id} не найден")
        return None
    
    try:
        # Обновление полей пользователя
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        # Обновление времени последней активности
        user.last_activity = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        logger.info(f"Обновлен профиль пользователя с telegram_id={telegram_id}")
        return user
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Ошибка при обновлении профиля пользователя: {e}")
        return None
