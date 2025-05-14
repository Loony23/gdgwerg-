#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Сервис для работы с AmoCRM API.
"""

import logging
import requests
from typing import Dict, Any, Optional

from config import AMOCRM_API_KEY, AMOCRM_DOMAIN

logger = logging.getLogger(__name__)

class AmoCRMService:
    """
    Сервис для взаимодействия с AmoCRM API.
    """
    
    def __init__(self):
        self.api_key = AMOCRM_API_KEY
        self.domain = AMOCRM_DOMAIN
        self.base_url = f"https://{self.domain}.amocrm.ru/api/v4"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_contact(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение контакта по ID.
        
        Args:
            contact_id: ID контакта в AmoCRM
            
        Returns:
            Dict: Данные контакта или None в случае ошибки
        """
        url = f"{self.base_url}/contacts/{contact_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении контакта из AmoCRM: {e}")
            return None
    
    def create_contact(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Создание нового контакта.
        
        Args:
            data: Данные для создания контакта
            
        Returns:
            Dict: Данные созданного контакта или None в случае ошибки
        """
        url = f"{self.base_url}/contacts"
        
        try:
            response = requests.post(url, headers=self.headers, json=[data])
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при создании контакта в AmoCRM: {e}")
            return None
    
    def update_contact(self, contact_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Обновление существующего контакта.
        
        Args:
            contact_id: ID контакта в AmoCRM
            data: Данные для обновления контакта
            
        Returns:
            Dict: Данные обновленного контакта или None в случае ошибки
        """
        url = f"{self.base_url}/contacts/{contact_id}"
        
        try:
            response = requests.patch(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при обновлении контакта в AmoCRM: {e}")
            return None
