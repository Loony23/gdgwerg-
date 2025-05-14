#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Обработчик ошибок для Telegram-бота.
"""

import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик ошибок бота.
    Логирует ошибки и отправляет сообщение пользователю.
    
    Args:
        update: Объект обновления от Telegram (может быть None)
        context: Контекст бота с информацией об ошибке
    """
    # Логирование ошибки
    logger.error(f"Произошла ошибка: {context.error}")
    logger.error(traceback.format_exc())
    
    # Отправка сообщения пользователю, если возможно
    if update and isinstance(update, Update) and update.effective_message:
        error_message = (
            "К сожалению, произошла ошибка при обработке вашего запроса. "
            "Пожалуйста, попробуйте еще раз позже или обратитесь в службу поддержки."
        )
        await update.effective_message.reply_text(error_message)
