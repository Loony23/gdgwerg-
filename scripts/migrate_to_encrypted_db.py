#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для миграции данных из незашифрованной базы данных в зашифрованную.
"""

import sys
import os
import logging
import sqlite3
import shutil
from datetime import datetime

# Добавление корневой директории проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pysqlcipher3 import dbapi2 as sqlcipher
from config import DB_ENCRYPTION_KEY

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def migrate_to_encrypted_db():
    """
    Миграция данных из незашифрованной базы данных в зашифрованную.
    """
    # Путь к файлу базы данных
    db_path = "bot_database.db"
    backup_path = f"bot_database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    # Проверка существования базы данных
    if not os.path.exists(db_path):
        logger.error(f"База данных {db_path} не найдена")
        return False
    
    try:
        # Создание резервной копии
        shutil.copy2(db_path, backup_path)
        logger.info(f"Создана резервная копия базы данных: {backup_path}")
        
        # Подключение к незашифрованной базе данных
        conn_src = sqlite3.connect(db_path)
        cursor_src = conn_src.cursor()
        
        # Получение списка таблиц
        cursor_src.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor_src.fetchall()
        
        if not tables:
            logger.warning("В базе данных нет таблиц")
            conn_src.close()
            return False
        
        # Создание временной зашифрованной базы данных
        temp_db_path = "temp_encrypted.db"
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        
        conn_dest = sqlcipher.connect(temp_db_path)
        cursor_dest = conn_dest.cursor()
        
        # Установка ключа шифрования
        cursor_dest.execute(f"PRAGMA key = '{DB_ENCRYPTION_KEY}'")
        
        # Миграция схемы и данных для каждой таблицы
        for table in tables:
            table_name = table[0]
            
            # Пропуск системных таблиц SQLite
            if table_name.startswith('sqlite_'):
                continue
            
            logger.info(f"Миграция таблицы: {table_name}")
            
            # Получение схемы таблицы
            cursor_src.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            create_table_sql = cursor_src.fetchone()[0]
            
            # Создание таблицы в зашифрованной базе данных
            cursor_dest.execute(create_table_sql)
            
            # Получение данных из таблицы
            cursor_src.execute(f"SELECT * FROM {table_name};")
            rows = cursor_src.fetchall()
            
            if rows:
                # Получение имен столбцов
                cursor_src.execute(f"PRAGMA table_info({table_name});")
                columns = cursor_src.fetchall()
                column_count = len(columns)
                
                # Создание заполнителей для SQL запроса (?, ?, ...)
                placeholders = ', '.join(['?' for _ in range(column_count)])
                
                # Вставка данных в зашифрованную базу данных
                for row in rows:
                    cursor_dest.execute(f"INSERT INTO {table_name} VALUES ({placeholders});", row)
            
            logger.info(f"Мигрировано {len(rows)} записей из таблицы {table_name}")
        
        # Фиксация изменений
        conn_dest.commit()
        
        # Закрытие соединений
        conn_src.close()
        conn_dest.close()
        
        # Замена оригинальной базы данных на зашифрованную
        os.remove(db_path)
        os.rename(temp_db_path, db_path)
        
        logger.info("Миграция в зашифрованную базу данных успешно завершена")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при миграции базы данных: {e}")
        return False

if __name__ == "__main__":
    print("Миграция данных в зашифрованную базу данных")
    print("ВНИМАНИЕ: Перед продолжением убедитесь, что у вас есть резервная копия базы данных!")
    print("Продолжить? (y/n)")
    
    choice = input().lower()
    if choice == 'y':
        success = migrate_to_encrypted_db()
        if success:
            print("Миграция успешно завершена")
        else:
            print("Миграция не удалась. Проверьте логи для получения дополнительной информации.")
    else:
        print("Миграция отменена")
