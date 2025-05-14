#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Сервис для работы с уведомлениями в базе данных PostgreSQL.
"""

import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db.models import Notification, Patient

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Сервис для работы с уведомлениями.
    """
    
    def __init__(self, db: Session):
        """
        Инициализация сервиса.
        
        Args:
            db: Сессия базы данных
        """
        self.db = db
    
    async def create_notification(
        self,
        patient_id: int,
        telegram_id: int,
        appointment_id: int,
        message_id: int
    ) -> Optional[Notification]:
        """
        Создание нового уведомления.
        
        Args:
            patient_id: ID пациента в базе данных
            telegram_id: ID пользователя в Telegram
            appointment_id: ID визита в МИС
            message_id: ID отправленного сообщения в Telegram
            
        Returns:
            Notification: Созданное уведомление или None в случае ошибки
        """
        try:
            notification = Notification(
                patient_id=patient_id,
                telegram_id=telegram_id,
                appointment_id=appointment_id,
                message_id=message_id,
                status="pending",
                sent_at=datetime.utcnow()
            )
            
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            
            logger.info(f"Создано уведомление для пациента {patient_id}, визит {appointment_id}")
            return notification
        
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Ошибка при создании уведомления: {e}")
            return None
    
    async def get_notification(self, notification_id: int) -> Optional[Notification]:
        """
        Получение уведомления по ID.
        
        Args:
            notification_id: ID уведомления
            
        Returns:
            Notification: Объект уведомления или None, если не найдено
        """
        try:
            return self.db.query(Notification).filter(Notification.id == notification_id).first()
        
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении уведомления: {e}")
            return None
    
    async def get_notification_by_appointment_and_telegram(
        self,
        appointment_id: int,
        telegram_id: int
    ) -> Optional[Notification]:
        """
        Получение уведомления по ID визита и ID пользователя в Telegram.
        
        Args:
            appointment_id: ID визита в МИС
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Notification: Объект уведомления или None, если не найдено
        """
        try:
            return self.db.query(Notification).filter(
                Notification.appointment_id == appointment_id,
                Notification.telegram_id == telegram_id
            ).first()
        
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении уведомления: {e}")
            return None
    
    async def update_notification_status(
        self,
        notification_id: int,
        status: str,
        responded_at: datetime = None,
        cancel_reason: str = None
    ) -> bool:
        """
        Обновление статуса уведомления.
        
        Args:
            notification_id: ID уведомления
            status: Новый статус уведомления
            responded_at: Время ответа пользователя
            cancel_reason: Причина отмены (если применимо)
            
        Returns:
            bool: True, если обновление успешно, иначе False
        """
        try:
            notification = await self.get_notification(notification_id)
            
            if not notification:
                logger.error(f"Уведомление с ID {notification_id} не найдено")
                return False
            
            notification.status = status
            
            if responded_at:
                notification.responded_at = responded_at
            
            if cancel_reason:
                notification.cancel_reason = cancel_reason
            
            self.db.commit()
            logger.info(f"Обновлен статус уведомления {notification_id} на {status}")
            return True
        
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Ошибка при обновлении статуса уведомления: {e}")
            return False
    
    async def get_pending_notifications_by_patient(self, patient_id: int) -> List[Notification]:
        """
        Получение всех ожидающих ответа уведомлений пациента.
        
        Args:
            patient_id: ID пациента в базе данных
            
        Returns:
            List[Notification]: Список уведомлений
        """
        try:
            return self.db.query(Notification).filter(
                Notification.patient_id == patient_id,
                Notification.status == "pending"
            ).all()
        
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении ожидающих уведомлений: {e}")
            return []
    
    async def get_notifications_by_status(self, status: str) -> List[Notification]:
        """
        Получение всех уведомлений с указанным статусом.
        
        Args:
            status: Статус уведомлений
            
        Returns:
            List[Notification]: Список уведомлений
        """
        try:
            return self.db.query(Notification).filter(
                Notification.status == status
            ).all()
        
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении уведомлений по статусу: {e}")
            return []
