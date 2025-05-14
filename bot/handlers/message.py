#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Обработчик текстовых сообщений для Telegram-бота.
"""

import logging
import re
from datetime import datetime
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from db.database import get_db
from bot.services.patient_service import get_patient_by_telegram_id, update_patient_profile, get_decrypted_patient_data
from bot.services.mis_service import MISService

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик текстовых сообщений.
    Обрабатывает сообщения в зависимости от текущего состояния пациента.
    
    Args:
        update: Объект обновления от Telegram
        context: Контекст бота
    """
    user = update.effective_user
    message_text = update.message.text
    logger.info(f"Получено сообщение от пользователя {user.id}: {message_text}")
    
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
    
    # Обработка сообщения в зависимости от текущего состояния пациента
    bot_state = db_patient.bot_state
    
    if bot_state in ["awaiting_notifications_consent", "awaiting_marketing_consent"]:
        # Если пациент находится в процессе получения согласий,
        # напоминаем ему нажать на кнопки
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки для ответа на вопросы о согласиях. "
            "Если кнопки не отображаются, используйте команду /start для повторного запуска."
        )
    
    elif bot_state == "awaiting_phone_number":
        # Обработка ввода номера телефона
        phone_number = message_text.strip()
        
        # Простая валидация номера телефона (только цифры, +, длина)
        if re.match(r'^\+?[0-9]{10,15}$', phone_number):
            # Сохраняем номер телефона (будет зашифрован в update_patient_profile)
            update_patient_profile(db, user.id, phone_number=phone_number, bot_state="awaiting_birth_date")
            
            logger.info(f"Пользователь {user.id} ввел номер телефона: {phone_number}")
            
            # Отправляем запрос на дату рождения
            await update.message.reply_text(
                "🎂 Пожалуйста, введите вашу дату рождения в формате ДД.ММ.ГГГГ.",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            # Неверный формат номера телефона
            await update.message.reply_text(
                "❌ Неверный формат номера телефона. Пожалуйста, введите номер в формате +7XXXXXXXXXX "
                "или нажмите кнопку для автоматической отправки."
            )
    
    elif bot_state == "awaiting_birth_date":
        # Обработка ввода даты рождения
        birth_date_str = message_text.strip()
        
        # Проверка формата даты (ДД.ММ.ГГГГ)
        try:
            birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y").date()
            
            # Проверка, что дата рождения не в будущем
            if birth_date > datetime.now().date():
                await update.message.reply_text(
                    "❌ Дата рождения не может быть в будущем. Пожалуйста, введите корректную дату в формате ДД.ММ.ГГГГ."
                )
                return
            
            # Сохраняем дату рождения (будет зашифрована в update_patient_profile)
            update_patient_profile(db, user.id, birth_date=birth_date)
            
            # Отправляем сообщение о поиске пациента в МИС
            await update.message.reply_text(
                "🔍 Ищем ваши данные в системе клиники..."
            )
            
            # Поиск пациента в МИС
            mis_service = MISService()
            
            # Используем метод get_patient_by_phone_and_birth_date с параметрами mobile и birth_date в формате ДД.ММ.ГГГГ
            patients = await mis_service.get_patient_by_phone_and_birth_date(
                patient_data.get('phone_number'), 
                birth_date_str  # Передаем дату в формате ДД.ММ.ГГГГ как получили от пользователя
            )
            
            if patients:
                logger.info(f"Пациент найден в МИС: {patients}")
                
                # Проверяем, является ли результат списком пациентов
                if isinstance(patients, list):
                    # Если найдено несколько пациентов, предлагаем пользователю выбрать
                    if len(patients) > 1:
                        await update.message.reply_text(
                            "👥 Мы нашли несколько пациентов с такими данными. Пожалуйста, выберите себя из списка:"
                        )
                        
                        # Создаем клавиатуру с кнопками для выбора пациента
                        buttons = []
                        for patient in patients:
                            patient_id = patient.get("patient_id")
                            name = f"{patient.get('last_name')} {patient.get('first_name')} {patient.get('third_name', '')}"
                            buttons.append([InlineKeyboardButton(name, callback_data=f"select_patient:{patient_id}")])
                        
                        keyboard = InlineKeyboardMarkup(buttons)
                        
                        # Отправляем сообщение с кнопками выбора пациента
                        await update.message.reply_text(
                            "Выберите пациента:",
                            reply_markup=keyboard
                        )
                        
                        # Устанавливаем состояние ожидания выбора пациента
                        update_patient_profile(db, user.id, bot_state="awaiting_patient_selection")
                        return
                    else:
                        # Если найден только один пациент, используем его
                        patient = patients[0]
                else:
                    # Если результат не список, а один пациент
                    patient = patients
                
                # Сохраняем данные пациента
                update_patient_profile(
                    db, 
                    user.id,
                    mis_id=patient.get("patient_id"),
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
                await update.message.reply_text(
                    f"✅ {greeting_name}, мы рады вас приветствовать в телеграм-боте Клиники психотерапии и психсоматики 🌞"
                )
            else:
                # Пациент не найден
                logger.warning(f"Пациент не найден в МИС по номеру телефона: {patient_data.get('phone_number')} и дате рождения: {birth_date_str}")
                update_patient_profile(db, user.id, bot_state="awaiting_phone_number")
                
                # Создаем кнопку для отправки контакта
                keyboard = ReplyKeyboardMarkup(
                    [[KeyboardButton("📱 Отправить номер телефона", request_contact=True)]],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
                
                # Отправляем сообщение об ошибке
                await update.message.reply_text(
                    "❗ Мы не смогли найти ваши данные. Пожалуйста, проверьте номер телефона и дату рождения или обратитесь в клинику.",
                    reply_markup=keyboard
                )
        except ValueError:
            # Неверный формат даты
            await update.message.reply_text(
                "❌ Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ."
            )
    
    else:  # active или другие состояния
        # Обработка обычных сообщений
        await update.message.reply_text(
            "Я получил ваше сообщение. Чтобы узнать о доступных командах, используйте /help."
        )
    
    # Закрытие сессии базы данных
    db.close()
