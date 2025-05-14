#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для просмотра данных в базе данных PostgreSQL.
"""

import sys
import os
import logging
from datetime import datetime
from tabulate import tabulate

# Добавление корневой директории проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from db.models import Patient, Service, Notification, WebhookEvent, Conversation
from bot.services.patient_service import get_decrypted_patient_data

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def view_patients():
    """
    Просмотр всех пациентов в базе данных.
    """
    db = SessionLocal()
    try:
        patients = db.query(Patient).all()
        
        if not patients:
            print("В базе данных нет пациентов.")
            return
        
        # Подготовка данных для таблицы
        headers = [
            "ID", "Telegram ID", "MIS ID", "AmoCRM ID", "Телефон", 
            "Имя", "Фамилия", "Отчество", "Дата рождения", 
            "Согласие на уведомления", "Согласие на маркетинг",
            "Состояние", "Дата регистрации", "Последняя активность"
        ]
        
        rows = []
        for patient in patients:
            # Получение расшифрованных данных пациента
            patient_data = get_decrypted_patient_data(db, patient)
            
            birth_date = patient_data.get('birth_date').strftime("%d.%m.%Y") if patient_data.get('birth_date') else "Не указана"
            registration_date = patient_data.get('registration_date').strftime("%d.%m.%Y %H:%M") if patient_data.get('registration_date') else "Не указана"
            last_activity = patient_data.get('last_activity').strftime("%d.%m.%Y %H:%M") if patient_data.get('last_activity') else "Не указана"
            
            rows.append([
                patient_data.get('id'), patient_data.get('telegram_id'), patient_data.get('mis_id'), patient_data.get('amocrm_id'),
                patient_data.get('phone_number'), patient_data.get('first_name'), patient_data.get('last_name'), patient_data.get('third_name'),
                birth_date, patient_data.get('consent_notifications'), patient_data.get('consent_marketing'),
                patient_data.get('bot_state'), registration_date, last_activity
            ])
        
        # Вывод таблицы
        print("\nСписок пациентов:")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print(f"Всего пациентов: {len(patients)}")
        
    except Exception as e:
        logger.error(f"Ошибка при получении данных пациентов: {e}")
    finally:
        db.close()

def view_notifications():
    """
    Просмотр всех уведомлений в базе данных.
    """
    db = SessionLocal()
    try:
        notifications = db.query(Notification).all()
        
        if not notifications:
            print("В базе данных нет уведомлений.")
            return
        
        # Подготовка данных для таблицы
        headers = [
            "ID", "Patient ID", "Telegram ID", "Appointment ID", "Message ID",
            "Статус", "Отправлено", "Отвечено", "Причина отмены"
        ]
        
        rows = []
        for notification in notifications:
            sent_at = notification.sent_at.strftime("%d.%m.%Y %H:%M") if notification.sent_at else "Не указано"
            responded_at = notification.responded_at.strftime("%d.%m.%Y %H:%M") if notification.responded_at else "Не указано"
            
            rows.append([
                notification.id, notification.patient_id, notification.telegram_id,
                notification.appointment_id, notification.message_id,
                notification.status, sent_at, responded_at, notification.cancel_reason
            ])
        
        # Вывод таблицы
        print("\nСписок уведомлений:")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print(f"Всего уведомлений: {len(notifications)}")
        
    except Exception as e:
        logger.error(f"Ошибка при получении данных уведомлений: {e}")
    finally:
        db.close()

def view_services():
    """
    Просмотр всех услуг в базе данных.
    """
    db = SessionLocal()
    try:
        services = db.query(Service).all()
        
        if not services:
            print("В базе данных нет услуг.")
            return
        
        # Подготовка данных для таблицы
        headers = [
            "ID", "Patient ID", "Дата", "Название услуги", "Врач", "Источник", "Обновлено"
        ]
        
        rows = []
        for service in services:
            date = service.date.strftime("%d.%m.%Y") if service.date else "Не указана"
            updated_at = service.updated_at.strftime("%d.%m.%Y %H:%M") if service.updated_at else "Не указано"
            
            rows.append([
                service.id, service.patient_id, date, service.service_name,
                service.doctor_name, service.source, updated_at
            ])
        
        # Вывод таблицы
        print("\nСписок услуг:")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print(f"Всего услуг: {len(services)}")
        
    except Exception as e:
        logger.error(f"Ошибка при получении данных услуг: {e}")
    finally:
        db.close()

def view_webhook_events():
    """
    Просмотр всех webhook-событий в базе данных.
    """
    db = SessionLocal()
    try:
        events = db.query(WebhookEvent).all()
        
        if not events:
            print("В базе данных нет webhook-событий.")
            return
        
        # Подготовка данных для таблицы
        headers = [
            "ID", "Тип события", "Получено"
        ]
        
        rows = []
        for event in events:
            received_at = event.received_at.strftime("%d.%m.%Y %H:%M") if event.received_at else "Не указано"
            
            rows.append([
                event.id, event.event_type, received_at
            ])
        
        # Вывод таблицы
        print("\nСписок webhook-событий:")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print(f"Всего событий: {len(events)}")
        
    except Exception as e:
        logger.error(f"Ошибка при получении данных webhook-событий: {e}")
    finally:
        db.close()

def view_patient_by_telegram_id(telegram_id):
    """
    Просмотр пациента по Telegram ID.
    
    Args:
        telegram_id: ID пользователя в Telegram
    """
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.telegram_id == telegram_id).first()
        
        if not patient:
            print(f"Пациент с Telegram ID {telegram_id} не найден.")
            return
        
        # Получение расшифрованных данных пациента
        patient_data = get_decrypted_patient_data(db, patient)
        
        # Вывод информации о пациенте
        birth_date = patient_data.get('birth_date').strftime("%d.%m.%Y") if patient_data.get('birth_date') else "Не указана"
        registration_date = patient_data.get('registration_date').strftime("%d.%m.%Y %H:%M") if patient_data.get('registration_date') else "Не указана"
        last_activity = patient_data.get('last_activity').strftime("%d.%m.%Y %H:%M") if patient_data.get('last_activity') else "Не указана"
        
        print("\nИнформация о пациенте:")
        print(f"ID в базе данных: {patient_data.get('id')}")
        print(f"Telegram ID: {patient_data.get('telegram_id')}")
        print(f"Telegram Chat ID: {patient_data.get('telegram_chat_id')}")
        print(f"Имя: {patient_data.get('first_name') or 'Не указано'}")
        print(f"Фамилия: {patient_data.get('last_name') or 'Не указана'}")
        print(f"Отчество: {patient_data.get('third_name') or 'Не указано'}")
        print(f"Номер телефона: {patient_data.get('phone_number') or 'Не указан'}")
        print(f"Дата рождения: {birth_date}")
        print(f"ID в МИС: {patient_data.get('mis_id') or 'Не привязан'}")
        print(f"ID в AmoCRM: {patient_data.get('amocrm_id') or 'Не привязан'}")
        print(f"Согласие на уведомления: {'Да' if patient_data.get('consent_notifications') else 'Нет'}")
        print(f"Согласие на маркетинг: {'Да' if patient_data.get('consent_marketing') else 'Нет'}")
        print(f"Текущее состояние: {patient_data.get('bot_state')}")
        print(f"Зарегистрирован в боте: {'Да' if patient_data.get('registered_in_bot') else 'Нет'}")
        print(f"Дата регистрации: {registration_date}")
        print(f"Последняя активность: {last_activity}")
        
    except Exception as e:
        logger.error(f"Ошибка при получении данных пациента: {e}")
    finally:
        db.close()

def main():
    """
    Основная функция скрипта.
    """
    print("Просмотр данных в базе данных PostgreSQL")
    print("1. Просмотр всех пациентов")
    print("2. Просмотр всех уведомлений")
    print("3. Просмотр всех услуг")
    print("4. Просмотр всех webhook-событий")
    print("5. Просмотр пациента по Telegram ID")
    print("0. Выход")
    
    choice = input("Выберите действие (0-5): ")
    
    if choice == "1":
        view_patients()
    elif choice == "2":
        view_notifications()
    elif choice == "3":
        view_services()
    elif choice == "4":
        view_webhook_events()
    elif choice == "5":
        telegram_id = input("Введите Telegram ID пациента: ")
        try:
            telegram_id = int(telegram_id)
            view_patient_by_telegram_id(telegram_id)
        except ValueError:
            print("Некорректный Telegram ID. Должно быть целое число.")
    elif choice == "0":
        print("Выход из программы.")
        return
    else:
        print("Некорректный выбор.")

if __name__ == "__main__":
    main()
