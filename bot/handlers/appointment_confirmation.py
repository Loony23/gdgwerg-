#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Обработчик для подтверждения и отмены визитов пациентов.
"""

import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from db.database import get_db
from bot.services.mis_service import MISService
from bot.services.notification_service import NotificationService
from bot.services.patient_service import get_patient_by_telegram_id, get_decrypted_patient_data

logger = logging.getLogger(__name__)

async def handle_appointment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для кнопок подтверждения и отмены визита.
    
    Args:
        update: Объект обновления от Telegram
        context: Контекст бота
    """
    query = update.callback_query
    await query.answer()  # Отвечаем на callback query, чтобы убрать часы загрузки
    
    # Получаем данные из callback_data
    callback_data = query.data
    try:
        action, appointment_id = callback_data.split(":")
        appointment_id = int(appointment_id)
    except (ValueError, IndexError) as e:
        logger.error(f"Некорректный формат callback_data: {callback_data}. Ошибка: {e}")
        await query.message.reply_text("Произошла ошибка при обработке запроса. Пожалуйста, попробуйте снова.")
        return
    
    # Получаем telegram_id пользователя
    telegram_id = update.effective_user.id
    
    # Инициализируем сервисы
    db = next(get_db())
    mis_service = MISService()
    notification_service = NotificationService(db)
    
    try:
        # Получаем уведомление по appointment_id и telegram_id
        notification = await notification_service.get_notification_by_appointment_and_telegram(
            appointment_id, telegram_id
        )
        
        if not notification:
            logger.error(f"Уведомление не найдено для appointment_id={appointment_id} и telegram_id={telegram_id}")
            await query.message.reply_text("Уведомление не найдено или устарело.")
            return
        
        # Получаем пациента из базы данных
        patient = get_patient_by_telegram_id(db, telegram_id)
        if not patient:
            logger.error(f"Пациент не найден для telegram_id={telegram_id}")
            await query.message.reply_text("Произошла ошибка при обработке запроса. Пожалуйста, попробуйте снова.")
            return
        
        # Получаем расшифрованные данные пациента
        patient_data = get_decrypted_patient_data(db, patient)
        
        # Обрабатываем действие в зависимости от типа кнопки
        if action == "confirm_appointment":
            # Подтверждение визита
            success = await mis_service.confirm_appointment(appointment_id)
            
            if success:
                # Обновляем статус уведомления
                await notification_service.update_notification_status(
                    notification.id,
                    "confirmed",
                    datetime.utcnow()
                )
                
                # Отправляем сообщение пользователю
                await query.message.edit_text(
                    "✅ Ваша запись успешно подтверждена!",
                    reply_markup=None  # Убираем кнопки
                )
                
                logger.info(f"Пользователь {telegram_id} подтвердил визит {appointment_id}")
            else:
                logger.error(f"Ошибка при подтверждении визита в МИС: appointment_id={appointment_id}")
                await query.message.reply_text(
                    "К сожалению, произошла ошибка при подтверждении записи. "
                    "Пожалуйста, свяжитесь с клиникой по телефону."
                )
        
        elif action == "cancel_appointment":
            # Отмена визита
            # Обновляем статус уведомления
            await notification_service.update_notification_status(
                notification.id,
                "cancelled",
                datetime.utcnow(),
                "cancelled_by_patient_needs_followup"
            )
            
            # Отправляем сообщение пользователю
            await query.message.edit_text(
                "❌ Очень жаль, будем ждать вас в следующий раз!",
                reply_markup=None  # Убираем кнопки
            )
            
            # Отменяем визит в МИС
            await mis_service.cancel_appointment(
                appointment_id,
                "cancelled_by_patient_needs_followup"
            )
            
            # Создаем задачу в МИС для связи с пациентом
            deadline = datetime.utcnow() + timedelta(days=1)
            await mis_service.create_task(
                patient_data.get('mis_id'),
                appointment_id,
                "Пациент отменил приём через Telegram",
                "Пациент отменил визит через Telegram-бот. Требуется связаться с пациентом и уточнить причину отмены.",
                deadline.strftime("%Y-%m-%d")
            )
            
            logger.info(f"Пользователь {telegram_id} отменил визит {appointment_id}")
        
        else:
            logger.warning(f"Неизвестное действие: {action}")
            await query.message.reply_text("Неизвестная команда. Пожалуйста, попробуйте снова.")
    
    except Exception as e:
        logger.error(f"Ошибка при обработке подтверждения/отмены визита: {e}")
        await query.message.reply_text(
            "К сожалению, произошла ошибка при обработке вашего запроса. "
            "Пожалуйста, свяжитесь с клиникой по телефону."
        )
    finally:
        db.close()

# Регистрация обработчика
appointment_confirmation_handler = CallbackQueryHandler(
    handle_appointment_confirmation,
    pattern=r"^(confirm_appointment|cancel_appointment):[0-9]+$"
)
