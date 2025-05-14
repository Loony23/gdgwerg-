#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Обработчик команды /help для Telegram-бота.
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from db.database import get_db
from bot.services.patient_service import get_patient_by_telegram_id

logger = logging.getLogger(__name__)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /help.
    Отображает справочную информацию о боте.
    
    Args:
        update: Объект обновления от Telegram
        context: Контекст бота
    """
    user = update.effective_user
    logger.info(f"Пользователь {user.id} запросил справку")
    
    # Обновление времени последней активности пациента
    db = next(get_db())
    db_patient = get_patient_by_telegram_id(db, user.id)
    if db_patient:
        db_patient.last_activity = datetime.utcnow()
        db.commit()
    
    # Справочное сообщение
    help_message = (
        "📋 *Справка по командам бота*\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
        "/profile - Просмотр и редактирование профиля\n"
        "/appointment - Запись на прием\n"
        "/results - Просмотр результатов анализов\n"
        "/notifications - Управление уведомлениями\n\n"
        "Если у вас возникли вопросы или проблемы, "
        "пожалуйста, обратитесь в службу поддержки клиники."
    )
    
    await update.message.reply_text(help_message, parse_mode='Markdown')
