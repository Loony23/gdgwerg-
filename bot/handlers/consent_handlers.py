#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Обработчики для согласий пациента.
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from db.database import get_db
from bot.services.patient_service import get_patient_by_telegram_id, update_patient_profile
from bot.utils.text_loader import load_text

logger = logging.getLogger(__name__)

async def handle_notifications_consent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик согласия на уведомления.
    
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
    
    # Получаем действие из callback_data
    action = query.data.split(":")[1]
    
    if action == "yes":
        # Пациент согласился на уведомления
        update_patient_profile(db, user.id, consent_notifications=True, bot_state="awaiting_marketing_consent")
        
        # Отправляем сообщение о принятии согласия
        await query.message.edit_text(
            "✅ Спасибо! Вы будете получать уведомления о важных событиях.",
            reply_markup=None
        )
        
        # Загружаем текст согласия на маркетинг
        consent_text = load_text('consent_marketing.md')
        
        # Создаем кнопки согласия/отказа
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Согласен", callback_data="consent_marketing:yes"),
                InlineKeyboardButton("❌ Не согласен", callback_data="consent_marketing:no")
            ]
        ])
        
        # Отправляем запрос на согласие на маркетинг
        await query.message.reply_text(consent_text, reply_markup=keyboard, parse_mode='Markdown')
    
    db.close()

async def handle_marketing_consent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик согласия на маркетинговые материалы.
    
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
    
    # Получаем действие из callback_data
    action = query.data.split(":")[1]
    
    # Обновляем состояние пациента
    consent_marketing = (action == "yes")
    update_patient_profile(db, user.id, consent_marketing=consent_marketing, bot_state="awaiting_phone_number")
    
    # Отправляем сообщение о принятии решения
    if action == "yes":
        await query.message.edit_text(
            "✅ Спасибо! Вы будете получать информацию о новых услугах и акциях.",
            reply_markup=None
        )
    else:
        await query.message.edit_text(
            "✅ Хорошо! Вы не будете получать маркетинговые материалы.",
            reply_markup=None
        )
    
    # Создаем кнопку для отправки контакта
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    # Отправляем запрос на номер телефона
    await query.message.reply_text(
        "📱 Пожалуйста, отправьте свой номер телефона для идентификации. "
        "Вы можете нажать кнопку ниже, чтобы передать номер автоматически.",
        reply_markup=keyboard
    )
    
    db.close()

# Регистрация обработчиков
notifications_consent_handler = CallbackQueryHandler(
    handle_notifications_consent,
    pattern=r"^consent_notifications:[a-z]+$"
)

marketing_consent_handler = CallbackQueryHandler(
    handle_marketing_consent,
    pattern=r"^consent_marketing:[a-z]+$"
)
