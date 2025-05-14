#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модели базы данных для Telegram-бота с использованием PostgreSQL и шифрования.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, Date, DateTime, ForeignKey, JSON, Text, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from db.database import Base

class Patient(Base):
    """
    Модель пациента в системе с шифрованием конфиденциальных данных.
    """
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    telegram_chat_id = Column(BigInteger, nullable=True)
    amocrm_id = Column(Integer, nullable=True)
    mis_id = Column(Integer, nullable=True)
    
    # Шифруемые поля (хранятся как BYTEA)
    phone_number = Column(LargeBinary, nullable=True)
    first_name = Column(LargeBinary, nullable=True)
    last_name = Column(LargeBinary, nullable=True)
    third_name = Column(LargeBinary, nullable=True)
    birth_date = Column(LargeBinary, nullable=True)
    
    # Нешифруемые поля
    consent_notifications = Column(Boolean, default=False)
    consent_marketing = Column(Boolean, default=False)
    bot_state = Column(String(50), default="new")
    registered_in_bot = Column(Boolean, default=False)
    registration_date = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=False, default=datetime.utcnow)
    initial_message_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Отношения
    services = relationship("Service", back_populates="patient", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="patient", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Patient(id={self.id}, telegram_id={self.telegram_id})>"


class Service(Base):
    """
    Модель услуги/посещения пациента.
    """
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    service_name = Column(String(255), nullable=False)
    doctor_name = Column(String(255), nullable=True)
    source = Column(String(50), nullable=False, default="mis")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношение с моделью Patient
    patient = relationship("Patient", back_populates="services")

    def __repr__(self):
        return f"<Service(id={self.id}, patient_id={self.patient_id}, service_name={self.service_name})>"


class Notification(Base):
    """
    Модель уведомления о приеме.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    telegram_id = Column(BigInteger, nullable=False)
    appointment_id = Column(Integer, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)
    cancel_reason = Column(String(255), nullable=True)

    # Отношение с моделью Patient
    patient = relationship("Patient", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, patient_id={self.patient_id}, status={self.status})>"


class WebhookEvent(Base):
    """
    Модель для логирования входящих событий от внешних систем.
    """
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=True)
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<WebhookEvent(id={self.id}, event_type={self.event_type}, received_at={self.received_at})>"


class Conversation(Base):
    """
    Модель для кеширования информации о чатах.
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    last_message = Column(Text, nullable=True)
    last_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    unread_count = Column(Integer, nullable=False, default=0)

    # Отношение с моделью Patient
    patient = relationship("Patient", back_populates="conversations")

    def __repr__(self):
        return f"<Conversation(id={self.id}, patient_id={self.patient_id}, unread_count={self.unread_count})>"
