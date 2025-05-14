#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Обработчик команды /profile для Telegram-бота.
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from db.database import get_db
from bot.services.patient_service import get_patient_by_telegram_id, get_decrypted_patient_data

logger = logging.getLogger(__name__)

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /profile.
    Отображает информацию о пациенте из базы данных.
    
    Args:
        update: Объект обновления от Telegram
        context: Контекст бота
    """
    user = update.effective_user
    logger.info(f"Пользователь {user.id} запросил свой профиль")
    
    # Получение пациента из базы данных
    db = next(get_db())
    db_patient = get_patient_by_telegram_id(db, user.id)
    
    if not db_patient:
        await update.message.reply_text(
            "Кажется, вы еще не зарегистрированы. Пожалуйста, используйте команду /start для начала работы с ботом."
        )
        return
    
    # Обновление времени последней активности
    db_patient.last_activity = datetime.utcnow()
    db.commit()
    
    # Получение расшифрованных данных пациента
    patient_data = get_decrypted_patient_data(db, db_patient)
    
    # Форматирование даты рождения
    birth_date = patient_data.get('birth_date').strftime("%d.%m.%Y") if patient_data.get('birth_date') else "Не указана"
    
    # Форматирование даты регистрации
    registration_date = patient_data.get('registration_date').strftime("%d.%m.%Y %H:%M") if patient_data.get('registration_date') else "Не указана"
    
    # Форматирование последней активности
    last_activity = patient_data.get('last_activity').strftime("%d.%m.%Y %H:%M") if patient_data.get('last_activity') else "Не указана"
    
    # Формирование сообщения с данными пациента
    profile_message = (
        "📋 *Ваш профиль в системе*\n\n"
        f"*ID в базе данных:* {patient_data.get('id')}\n"
        f"*Telegram ID:* {patient_data.get('telegram_id')}\n"
        f"*Имя:* {patient_data.get('first_name') or 'Не указано'}\n"
        f"*Фамилия:* {patient_data.get('last_name') or 'Не указана'}\n"
        f"*Отчество:* {patient_data.get('third_name') or 'Не указано'}\n"
        f"*Номер телефона:* {patient_data.get('phone_number') or 'Не указан'}\n"
        f"*Дата рождения:* {birth_date}\n"
        f"*ID в МИС:* {patient_data.get('mis_id') or 'Не привязан'}\n"
        f"*ID в AmoCRM:* {patient_data.get('amocrm_id') or 'Не привязан'}\n"
        f"*Согласие на уведомления:* {'Да' if patient_data.get('consent_notifications') else 'Нет'}\n"
        f"*Согласие на маркетинг:* {'Да' if patient_data.get('consent_marketing') else 'Нет'}\n"
        f"*Текущее состояние:* {patient_data.get('bot_state')}\n"
        f"*Дата регистрации:* {registration_date}\n"
        f"*Последняя активность:* {last_activity}\n"
    )
    
    await update.message.reply_text(profile_message, parse_mode='Markdown')

# Создание обработчика команды
profile_handler = CommandHandler("profile", profile_command)
