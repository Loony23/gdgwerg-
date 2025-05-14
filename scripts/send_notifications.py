#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для отправки уведомлений пользователям.
Может быть запущен по расписанию через cron или другой планировщик.
"""

import logging
import sys
import os
import asyncio
from datetime import datetime, timedelta
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session

# Добавление корневой директории проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TELEGRAM_BOT_TOKEN
from db.database import SessionLocal
from db.models import Patient
from bot.services.mis_service import MISService
from bot.services.notification_service import NotificationService
from bot.services.patient_service import get_decrypted_patient_data

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='notifications.log'
)
logger = logging.getLogger(__name__)

async def send_appointment_reminders():
    """
    Отправка напоминаний о предстоящих приемах.
    """
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    db = SessionLocal()
    mis_service = MISService()
    notification_service = NotificationService(db)
    
    try:
        # Получение пациентов, которые согласились на уведомления
        patients = db.query(Patient).filter(Patient.consent_notifications == True).all()
        
        for patient in patients:
            # Получаем расшифрованные данные пациента
            patient_data = get_decrypted_patient_data(db, patient)
            
            if not patient_data.get('mis_id'):
                continue
            
            # Получение предстоящих приемов из МИС
            appointments = await mis_service.get_appointments(patient_data.get('mis_id'))
            if not appointments:
                continue
            
            # Фильтрация приемов, которые состоятся завтра
            tomorrow = datetime.now().date() + timedelta(days=1)
            tomorrow_appointments = [
                app for app in appointments 
                if datetime.fromisoformat(app['date']).date() == tomorrow
            ]
            
            # Отправка уведомлений о приемах
            for appointment in tomorrow_appointments:
                doctor_name = appointment.get('doctor_name', 'специалиста')
                time = datetime.fromisoformat(appointment['date']).strftime('%H:%M')
                appointment_id = appointment.get('id')
                
                # Создаем клавиатуру с кнопками подтверждения/отмены
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Подтверждаю", callback_data=f"confirm_appointment:{appointment_id}"),
                        InlineKeyboardButton("❌ Отменяю", callback_data=f"cancel_appointment:{appointment_id}")
                    ]
                ])
                
                message = (
                    f"Напоминание о записи на прием!\n\n"
                    f"Завтра в {time} у вас прием к {doctor_name}.\n"
                    f"Адрес клиники: {appointment.get('clinic_address', 'уточните в регистратуре')}.\n\n"
                    f"Пожалуйста, подтвердите или отмените ваш визит:"
                )
                
                # Отправляем сообщение с кнопками
                chat_id = patient_data.get('telegram_chat_id') or patient_data.get('telegram_id')
                sent_message = await bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    reply_markup=keyboard
                )
                
                # Сохраняем информацию об отправленном уведомлении
                await notification_service.create_notification(
                    patient_id=patient_data.get('id'),
                    telegram_id=patient_data.get('telegram_id'),
                    appointment_id=appointment_id,
                    message_id=sent_message.message_id
                )
                
                logger.info(f"Отправлено напоминание пациенту {patient_data.get('telegram_id')} о приеме завтра в {time}")
    
    except Exception as e:
        logger.error(f"Ошибка при отправке напоминаний: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Запуск скрипта отправки уведомлений")
    asyncio.run(send_appointment_reminders())
    logger.info("Скрипт отправки уведомлений завершен")
