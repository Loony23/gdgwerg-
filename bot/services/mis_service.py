#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Сервис для работы с API МИС Renovatio.
"""

import logging
import httpx
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from config import MIS_RENOVATIO_API_KEY

logger = logging.getLogger(__name__)

class MISService:
    """
    Сервис для взаимодействия с API МИС Renovatio.
    """
    
    def __init__(self):
        self.api_key = MIS_RENOVATIO_API_KEY
        self.base_url = "https://app.rnova.org/api/public"
        self.api_version = "v2"
        self.timeout = 10.0
    
    async def _make_request(self, method: str, params: Dict[str, Any], version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Выполнение запроса к API МИС Renovatio.
        
        Args:
            method: Метод API
            params: Параметры запроса
            version: Версия API (если None, версия не указывается в URL)
            
        Returns:
            Dict: Данные ответа или None в случае ошибки
        """
        # Используем переданную версию или версию по умолчанию
        api_version = version if version is not None else self.api_version
        
        # Формируем URL с учетом версии API
        url = f"{self.base_url}/{api_version}/{method}" if api_version else f"{self.base_url}/{method}"
        
        # Добавляем API ключ к параметрам
        params["api_key"] = self.api_key
        
        # Логирование запроса (без API ключа для безопасности)
        log_params = params.copy()
        if "api_key" in log_params:
            log_params["api_key"] = "***HIDDEN***"
        logger.info(f"Отправка запроса к МИС: {url}, параметры: {log_params}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Используем правильный формат кодировки тела запроса: application/x-www-form-urlencoded
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                response = await client.post(url, data=params, headers=headers)
            
            # Логирование статуса ответа
            logger.info(f"Получен ответ от МИС: статус {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            
            # Логирование результата (без конфиденциальных данных)
            if "error" in result:
                logger.info(f"Результат запроса: error={result.get('error')}")
            
            # Проверяем наличие ошибок в ответе
            if result.get("error") == 1:
                error_data = result.get("data", {})
                logger.error(f"Ошибка API МИС: код={error_data.get('code')}, описание={error_data.get('desc')}")
                return None
            
            logger.info(f"Успешный запрос к МИС: получены данные")
            return result.get("data")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Ошибка HTTP при запросе к МИС: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Ошибка запроса к МИС: {e}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка при запросе к МИС: {e}")
            return None
    
    async def get_patient(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение данных пациента по ID.
        
        Args:
            patient_id: ID пациента в МИС
            
        Returns:
            Dict: Данные пациента или None в случае ошибки
        """
        params = {
            "patient_id": patient_id
        }
        
        return await self._make_request("getPatient", params)
    
    async def get_patient_by_phone_and_birth_date(self, mobile: str, birth_date: str) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """
        Получение данных пациента по номеру телефона и дате рождения.
        
        Args:
            mobile: Номер телефона пациента
            birth_date: Дата рождения в формате ДД.ММ.ГГГГ
            
        Returns:
            Union[Dict, List[Dict]]: Данные пациента (один пациент или список пациентов) или None в случае ошибки
        """
        # Форматирование номера телефона (удаление пробелов, скобок и т.д.)
        mobile = ''.join(filter(lambda x: x.isdigit() or x == '+', mobile))
        
        # Проверка формата номера телефона
        if not mobile.startswith('+'):
            # Добавляем + если его нет
            if mobile.startswith('7') or mobile.startswith('8'):
                mobile = '+7' + mobile[1:]
            else:
                mobile = '+7' + mobile
        
        logger.info(f"Поиск пациента по номеру телефона: {mobile} и дате рождения: {birth_date}")
        
        params = {
            "mobile": mobile,
            "birth_date": birth_date
        }
        
        # ВАЖНО: Явно указываем пустую строку для версии, чтобы запрос был отправлен без версии API
        result = await self._make_request("getPatient", params, version="")
        
        # Подробное логирование результата
        if result:
            if isinstance(result, list):
                logger.info(f"Найдено {len(result)} пациентов")
            elif "id" in result:
                logger.info(f"Пациент найден: ID={result.get('id')}, "
                           f"имя={result.get('first_name')}, "
                           f"фамилия={result.get('last_name')}")
            else:
                logger.info(f"Получен ответ от МИС, но пациент не найден")
        else:
            logger.warning(f"Пациент не найден или произошла ошибка при запросе")
        
        return result
    
    async def get_appointments(self, patient_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Получение списка приемов пациента.
        
        Args:
            patient_id: ID пациента в МИС
            
        Returns:
            List[Dict]: Список приемов или None в случае ошибки
        """
        params = {
            "patient_id": patient_id
        }
        
        result = await self._make_request("getAppointments", params)
        return result.get("appointments", []) if result else None
    
    async def get_test_results(self, patient_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Получение результатов анализов пациента.
        
        Args:
            patient_id: ID пациента в МИС
            
        Returns:
            List[Dict]: Список результатов анализов или None в случае ошибки
        """
        params = {
            "patient_id": patient_id
        }
        
        result = await self._make_request("getTestResults", params)
        return result.get("results", []) if result else None
    
    async def confirm_appointment(self, appointment_id: int) -> bool:
        """
        Подтвердить визит пациента в МИС Renovatio.
        
        Args:
            appointment_id: ID визита, который нужно подтвердить
            
        Returns:
            bool: True, если подтверждение успешно, иначе False
        """
        params = {
            "appointment_id": appointment_id,
            "source": "telegram_bot"  # указываем источник для отчётности
        }
        
        result = await self._make_request("confirmAppointment", params)
        return result is not None
    
    async def cancel_appointment(self, appointment_id: int, reason: str = None) -> bool:
        """
        Отменить визит пациента в МИС Renovatio.
        
        Args:
            appointment_id: ID визита, который нужно отменить
            reason: Причина отмены (опционально)
            
        Returns:
            bool: True, если отмена успешна, иначе False
        """
        params = {
            "appointment_id": appointment_id,
            "source": "telegram_bot"
        }
        
        if reason:
            params["reason"] = reason
        
        result = await self._make_request("cancelAppointment", params)
        return result is not None
    
    async def get_available_slots(self, doctor_id: int, date_from: str, date_to: str = None) -> Optional[List[Dict[str, Any]]]:
        """
        Получение доступных слотов для записи к врачу.
        
        Args:
            doctor_id: ID врача
            date_from: Дата начала периода в формате YYYY-MM-DD
            date_to: Дата окончания периода в формате YYYY-MM-DD (опционально)
            
        Returns:
            List[Dict]: Список доступных слотов или None в случае ошибки
        """
        params = {
            "doctor_id": doctor_id,
            "date_from": date_from
        }
        
        if date_to:
            params["date_to"] = date_to
        
        result = await self._make_request("getAvailableSlots", params)
        return result.get("slots", []) if result else None
    
    async def create_appointment(self, patient_id: int, doctor_id: int, datetime_slot: str) -> Optional[Dict[str, Any]]:
        """
        Создание записи на прием.
        
        Args:
            patient_id: ID пациента
            doctor_id: ID врача
            datetime_slot: Дата и время слота в формате YYYY-MM-DD HH:MM:SS
            
        Returns:
            Dict: Данные созданной записи или None в случае ошибки
        """
        params = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "datetime": datetime_slot,
            "source": "telegram_bot"
        }
        
        return await self._make_request("createAppointment", params)
    
    async def create_task(
        self,
        patient_id: int,
        appointment_id: int,
        title: str,
        description: str,
        deadline: str
    ) -> Optional[Dict[str, Any]]:
        """
        Создание задачи в МИС Renovatio.
        
        Args:
            patient_id: ID пациента
            appointment_id: ID визита
            title: Заголовок задачи
            description: Описание задачи
            deadline: Срок выполнения в формате YYYY-MM-DD
            
        Returns:
            Dict: Данные созданной задачи или None в случае ошибки
        """
        params = {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "title": title,
            "description": description,
            "deadline": deadline,
            "source": "telegram_bot"
        }
        
        return await self._make_request("createTask", params)
