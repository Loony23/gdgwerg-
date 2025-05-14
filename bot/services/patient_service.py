#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Сервис для работы с пациентами в базе данных PostgreSQL с шифрованием.
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, func

from db.models import Patient
from db.database import encrypt_text, decrypt_text

logger = logging.getLogger(__name__)

def get_patient_by_telegram_id(db: Session, telegram_id: int) -> Patient:
    """
    Получение пациента по Telegram ID.
    
    Args:
        db: Сессия базы данных
        telegram_id: ID пользователя в Telegram
        
    Returns:
        Patient: Объект пациента или None, если пациент не найден
    """
    try:
        return db.query(Patient).filter(Patient.telegram_id == telegram_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при получении пациента: {e}")
        return None

def get_or_create_patient(db: Session, telegram_id: int, telegram_chat_id: int = None) -> Patient:
    """
    Получение существующего пациента или создание нового.
    
    Args:
        db: Сессия базы данных
        telegram_id: ID пользователя в Telegram
        telegram_chat_id: ID чата в Telegram (опционально)
        
    Returns:
        Patient: Объект пациента
    """
    patient = get_patient_by_telegram_id(db, telegram_id)
    
    if not patient:
        # Создание нового пациента
        now = datetime.utcnow()
        patient = Patient(
            telegram_id=telegram_id,
            telegram_chat_id=telegram_chat_id,
            created_at=now,
            last_activity=now,
            bot_state="new"
        )
        try:
            db.add(patient)
            db.commit()
            db.refresh(patient)
            logger.info(f"Создан новый пациент с telegram_id={telegram_id}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Ошибка при создании пациента: {e}")
            raise
    
    return patient

def update_patient_profile(db: Session, telegram_id: int, **kwargs) -> Patient:
    """
    Обновление профиля пациента с шифрованием конфиденциальных данных.
    
    Args:
        db: Сессия базы данных
        telegram_id: ID пользователя в Telegram
        **kwargs: Поля для обновления (phone_number, first_name, и т.д.)
        
    Returns:
        Patient: Обновленный объект пациента
    """
    patient = get_patient_by_telegram_id(db, telegram_id)
    
    if not patient:
        logger.error(f"Пациент с telegram_id={telegram_id} не найден")
        return None
    
    try:
        # Шифруемые поля
        encrypted_fields = ['phone_number', 'first_name', 'last_name', 'third_name', 'birth_date']
        
        # Обновление полей пациента
        for key, value in kwargs.items():
            if hasattr(patient, key):
                if key in encrypted_fields and value is not None:
                    # Шифрование конфиденциальных данных
                    if key == 'birth_date' and isinstance(value, datetime):
                        # Преобразование даты в строку для шифрования
                        value_str = value.strftime("%Y-%m-%d")
                        encrypted_value = db.execute(encrypt_text(value_str)).scalar()
                    else:
                        encrypted_value = db.execute(encrypt_text(str(value))).scalar()
                    
                    setattr(patient, key, encrypted_value)
                else:
                    setattr(patient, key, value)
        
        # Обновление времени последней активности
        patient.last_activity = datetime.utcnow()
        
        db.commit()
        db.refresh(patient)
        logger.info(f"Обновлен профиль пациента с telegram_id={telegram_id}")
        return patient
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Ошибка при обновлении профиля пациента: {e}")
        return None

def get_decrypted_patient_data(db: Session, patient: Patient) -> dict:
    """
    Получение расшифрованных данных пациента.
    
    Args:
        db: Сессия базы данных
        patient: Объект пациента
        
    Returns:
        dict: Словарь с расшифрованными данными пациента
    """
    if not patient:
        return {}
    
    result = {
        'id': patient.id,
        'telegram_id': patient.telegram_id,
        'telegram_chat_id': patient.telegram_chat_id,
        'amocrm_id': patient.amocrm_id,
        'mis_id': patient.mis_id,
        'consent_notifications': patient.consent_notifications,
        'consent_marketing': patient.consent_marketing,
        'bot_state': patient.bot_state,
        'registered_in_bot': patient.registered_in_bot,
        'registration_date': patient.registration_date,
        'last_activity': patient.last_activity,
        'initial_message_sent': patient.initial_message_sent,
        'created_at': patient.created_at
    }
    
    # Расшифровка конфиденциальных данных
    if patient.phone_number:
        result['phone_number'] = db.execute(decrypt_text(patient.phone_number)).scalar()
    else:
        result['phone_number'] = None
        
    if patient.first_name:
        result['first_name'] = db.execute(decrypt_text(patient.first_name)).scalar()
    else:
        result['first_name'] = None
        
    if patient.last_name:
        result['last_name'] = db.execute(decrypt_text(patient.last_name)).scalar()
    else:
        result['last_name'] = None
        
    if patient.third_name:
        result['third_name'] = db.execute(decrypt_text(patient.third_name)).scalar()
    else:
        result['third_name'] = None
        
    if patient.birth_date:
        birth_date_str = db.execute(decrypt_text(patient.birth_date)).scalar()
        if birth_date_str:
            try:
                result['birth_date'] = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            except ValueError:
                result['birth_date'] = None
        else:
            result['birth_date'] = None
    else:
        result['birth_date'] = None
    
    return result

def search_patients(db: Session, query: str, limit: int = 10) -> list:
    """
    Поиск пациентов по имени, фамилии или номеру телефона.
    
    Args:
        db: Сессия базы данных
        query: Строка поиска
        limit: Максимальное количество результатов
        
    Returns:
        list: Список пациентов, соответствующих запросу
    """
    try:
        # Поиск по telegram_id (если query - число)
        if query.isdigit():
            patients = db.query(Patient).filter(Patient.telegram_id == int(query)).limit(limit).all()
            if patients:
                return [get_decrypted_patient_data(db, patient) for patient in patients]
        
        # Поиск по зашифрованным полям сложнее, так как нельзя напрямую искать в зашифрованных данных
        # Для этого нужно использовать специальные индексы или другие методы
        # В данном случае, мы можем расшифровать все записи и фильтровать их в памяти
        # Это не эффективно для больших баз данных, но работает для небольших наборов данных
        
        all_patients = db.query(Patient).limit(100).all()  # Ограничиваем выборку для производительности
        
        results = []
        for patient in all_patients:
            decrypted_data = get_decrypted_patient_data(db, patient)
            
            # Проверяем, содержит ли какое-либо из полей строку запроса
            if any(
                field and query.lower() in str(field).lower()
                for field in [
                    decrypted_data.get('first_name'),
                    decrypted_data.get('last_name'),
                    decrypted_data.get('third_name'),
                    decrypted_data.get('phone_number')
                ]
            ):
                results.append(decrypted_data)
                
                if len(results) >= limit:
                    break
        
        return results
    
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при поиске пациентов: {e}")
        return []
