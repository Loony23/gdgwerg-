#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Обработчик команды /start и логики поэтапной регистрации.
"""

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from db.database import get_db
from bot.services.patient_service import create_or_get_patient, update_patient_profile

def get_phone_request_keyboard():
    button = KeyboardButton(text="📱 Отправить номер", request_contact=True)
    return ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт команды /start"""
    user = update.effective_user
    db = next(get_db())
    patient = create_or_get_patient(db, user.id)

    await update.message.reply_text(
        "👋 Привет! Чтобы продолжить, подтвердите согласие на обработку персональных данных и получение уведомлений.\n\n"
        "Напиши: *Согласен*",
        parse_mode='Markdown'
    )
    update_patient_profile(db, patient, bot_state="awaiting_consent")


async def handle_consent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip().lower()

    db = next(get_db())
    patient = create_or_get_patient(db, user.id)

    if patient.bot_state != "awaiting_consent":
        return

    if "согласен" not in text:
        await update.message.reply_text("Пожалуйста, напиши 'Согласен', чтобы продолжить.")
        return

    update_patient_profile(db, patient, bot_state="awaiting_full_name")
    await update.message.reply_text("Отлично! Теперь напиши своё полное ФИО.")


async def handle_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    full_name = update.message.text.strip()

    db = next(get_db())
    patient = create_or_get_patient(db, user.id)

    if patient.bot_state != "awaiting_full_name":
        return

    update_patient_profile(db, patient, full_name=full_name, bot_state="awaiting_phone_number")

    await update.message.reply_text(
        f"Спасибо, {full_name}!\nТеперь отправьте свой номер телефона с помощью кнопки ниже ⬇️",
        reply_markup=get_phone_request_keyboard()
    )


def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_consent))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_full_name))
