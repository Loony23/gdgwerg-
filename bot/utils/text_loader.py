#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Утилита для загрузки текстовых файлов.
"""

import os
import logging

logger = logging.getLogger(__name__)

def load_text(filename: str) -> str:
    """
    Загружает текст из файла .md.

    Args:
        filename: Имя файла, например 'consent_notifications.md'

    Returns:
        Строка с текстом файла
    """
    base_path = os.path.join(os.path.dirname(__file__), '..', 'texts')
    file_path = os.path.join(base_path, filename)

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"Файл {file_path} не найден")
        return f"Ошибка: файл {filename} не найден"
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path}: {e}")
        return "Произошла ошибка при загрузке текста"

def reload_texts() -> None:
    """
    Перезагружает все тексты из папки texts.
    Полезно при обновлении текстов без перезапуска бота.
    """
    texts_dir = os.path.join(os.path.dirname(__file__), '..', 'texts')

    if not os.path.exists(texts_dir):
        logger.warning(f"Директория {texts_dir} не существует")
        return

    loaded_files = 0
    for filename in os.listdir(texts_dir):
        if filename.endswith('.md') or filename.endswith('.txt'):
            _ = load_text(filename)
            loaded_files += 1

    logger.info(f"Проверено {loaded_files} текстовых файлов")
