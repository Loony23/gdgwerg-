#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Настройка и инициализация Telegram-бота.
"""

import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.handlers.start import start_command
from bot.handlers.help import help_command
from bot.handlers.profile import profile_command
from bot.handlers.message import handle_message
from bot.handlers.error import error_handler
from bot.handlers.appointment_confirmation import appointment_confirmation_handler
from bot.handlers.consent_handlers import notifications_consent_handler, marketing_consent_handler
from bot.handlers.contact_handler import contact_handler
from bot.handlers.patient_selection import patient_selection_handler
from bot.utils.text_loader import reload_texts

logger = logging.getLogger(__name__)

def setup_bot(application: Application):
    """
    Настройка обработчиков команд и сообщений для бота.
    
    Args:
        application: Экземпляр приложения Telegram бота
    """
    logger.info("Настройка обработчиков команд и сообщений...")
    
    # Загрузка текстовых файлов
    reload_texts()
    logger.info("Текстовые файлы загружены")
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", profile_command))
    
    # Регистрация обработчиков согласий
    application.add_handler(notifications_consent_handler)
    application.add_handler(marketing_consent_handler)
    
    # Регистрация обработчика для подтверждения/отмены визитов
    application.add_handler(appointment_confirmation_handler)
    
    # Регистрация обработчика контактов
    application.add_handler(contact_handler)
    
    # Регистрация обработчика выбора пациента
    application.add_handler(patient_selection_handler)
    
    # Регистрация обработчика текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Регистрация обработчика ошибок
    application.add_error_handler(error_handler)
    
    logger.info("Бот успешно настроен")
