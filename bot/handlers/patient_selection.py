#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Обработчик для выбора пациента из списка.
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from db.database import get_db
from bot.services.patient_service import get_patient_by_telegram_id, update_patient_profile, get_decrypted_patient_data
from bot.services.mis_service import MISService

logger = logging.getLogger(__name__)

async def handle_patient_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для выбора пациента из списка.
    
    Args:
        update: Объект обновления от Telegram
        context: Контекст бота
    """
    query = update.callback_query
    await query.answer()  # Отвечаем на callback query, чтобы убрать часы загрузки
    
    user = update.effective_user
    db = next(get_db())
    db_patient = get_patient_by_telegram_id(db, user.id)
    
    if not db_patient:
        logger.error(f"Пациент с telegram_id={user.id} не найден")
        await query.message.reply_text("Произошла ошибка. Пожалуйста, используйте команду /start для начала работы с ботом.")
        return
    
    # Проверяем состояние пациента
    if db_patient.bot_state != "awaiting_patient_selection":
        await query.message.reply_text("Произошла ошибка. Пожалуйста, используйте команду /start для начала работы с ботом.")
        return
    
    # Получаем ID пациента из callback_data
    try:
        patient_id = int(query.data.split(":")[1])
    except (ValueError, IndexError) as e:
        logger.error(f"Некорректный формат callback_data: {query.data}. Ошибка: {e}")
        await query.message.reply_text("Произошла ошибка при обработке запроса. Пожалуйста, попробуйте снова.")
        return
    
    # Получаем данные пациента из МИС
    mis_service = MISService()
    patient = await mis_service.get_patient(patient_id)
    
    if patient:
        # Сохраняем данные пациента
        update_patient_profile(
            db, 
            user.id,
            mis_id=patient_id,
            first_name=patient.get("first_name"),
            last_name=patient.get("last_name"),
            third_name=patient.get("third_name"),
            bot_state="active",
            registration_date=datetime.utcnow(),  # Устанавливаем дату регистрации
            registered_in_bot=True
        )
        
        # Получаем обновленные данные пациента
        db_patient = get_patient_by_telegram_id(db, user.id)
        patient_data = get_decrypted_patient_data(db, db_patient)
        
        # Формируем имя и отчество для приветствия
        first_name = patient_data.get("first_name", "")
        third_name = patient_data.get("third_name", "")
        greeting_name = f"{first_name}"
        if third_name:
            greeting_name += f" {third_name}"
        
        # Отправляем приветственное сообщение
        await query.message.edit_text(
            f"✅ {greeting_name}, мы рады вас приветствовать в телеграм-боте Клиники психотерапии и психсоматики 🌞"
        )
    else:
        # Пациент не найден
        logger.error(f"Пациент с ID={patient_id} не найден в МИС")
        update_patient_profile(db, user.id, bot_state="awaiting_phone_number")
        
        # Отправляем сообщение об ошибке
        await query.message.edit_text(
            "❗ Произошла ошибка при получении данных пациента. Пожалуйста, попробуйте снова или обратитесь в клинику."
        )
    
    db.close()

# Регистрация обработчика
patient_selection_handler = CallbackQueryHandler(
    handle_patient_selection,
    pattern=r"^select_patient:[0-9]+$"
)
