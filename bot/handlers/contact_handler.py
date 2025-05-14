#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Обработчик для получения контакта пациента.
"""

import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, MessageHandler, filters

from db.database import get_db
from bot.services.patient_service import get_patient_by_telegram_id, update_patient_profile

logger = logging.getLogger(__name__)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    contact = update.message.contact

    if contact.user_id != user.id:
        await update.message.reply_text(
            "❌ Пожалуйста, отправьте свой собственный контакт, используя кнопку ниже.",
            reply_markup=None
        )
        return

    db = next(get_db())
    db_patient = get_patient_by_telegram_id(db, user.id)

    if not db_patient:
        await update.message.reply_text(
            "Кажется, вы еще не зарегистрированы. Пожалуйста, используйте команду /start."
        )
        return

    if db_patient.bot_state == "awaiting_phone_number":
        update_patient_profile(db, db_patient, phone_number=contact.phone_number, bot_state="registered")
        await update.message.reply_text(
            "✅ Ваш номер телефона сохранён! Регистрация завершена.",
            reply_markup=ReplyKeyboardRemove()
        )


async def reject_manual_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❗ Пожалуйста, используйте кнопку для отправки номера телефона — не вводите его вручную."
    )


def register_handlers(application):
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), reject_manual_phone))
