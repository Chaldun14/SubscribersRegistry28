# database.py (обновленная версия с хешированием паролей и ролями)
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import threading
from password_hasher import PasswordHasher, verify_password, hash_password
from logger import app_logger, log_query_time


class Database:
    """Класс для работы с базой данных SQLite с поддержкой многопоточности"""

    # Хранилище соединений для разных потоков
    _local = threading.local()

    def __init__(self, db_path="subscribers.db"):
        """Инициализация подключения к БД"""
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        """Получение соединения для текущего потока"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
            self._local.cursor = self._local.conn.cursor()
        return self._local.conn, self._local.cursor

    def _init_db(self):
        """Инициализация базы данных (создание таблиц)"""
        conn, cursor = self._get_connection()
        self.create_tables()
        self.init_default_data()

    def close(self):
        """Закрытие соединения с БД для текущего потока"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            delattr(self._local, 'conn')
            delattr(self._local, 'cursor')

    def commit(self):
        """Сохранение изменений"""
        if hasattr(self._local, 'conn'):
            self._local.conn.commit()

    @log_query_time
    def create_tables(self):
        """Создание таблиц, если их нет"""
        conn, cursor = self._get_connection()
        try:
            # Таблица пользователей для авторизации (с поддержкой хеширования)
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS users
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               username
                               TEXT
                               UNIQUE
                               NOT
                               NULL,
                               password
                               TEXT
                               NOT
                               NULL,
                               full_name
                               TEXT,
                               role
                               TEXT
                               DEFAULT
                               'viewer',
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               last_login
                               TIMESTAMP,
                               is_active
                               INTEGER
                               DEFAULT
                               1
                           )
                           ''')

            # Таблица для аудита действий
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS audit_log
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               user_id
                               INTEGER,
                               username
                               TEXT,
                               action
                               TEXT
                               NOT
                               NULL,
                               details
                               TEXT,
                               ip_address
                               TEXT,
                               timestamp
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               FOREIGN
                               KEY
                           (
                               user_id
                           ) REFERENCES users
                           (
                               id
                           )
                               )
                           ''')

            # Таблица клиентов
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS clients
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               full_name
                               TEXT
                               NOT
                               NULL,
                               address
                               TEXT
                               NOT
                               NULL,
                               phone
                               TEXT
                               NOT
                               NULL
                               UNIQUE,
                               email
                               TEXT,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           ''')

            # Таблица услуг
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS services
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               name
                               TEXT
                               NOT
                               NULL
                               UNIQUE,
                               type
                               TEXT
                               NOT
                               NULL,
                               cost
                               REAL
                               NOT
                               NULL
                               CHECK
                           (
                               cost >
                               0
                           ),
                               description TEXT
                               )
                           ''')

            # Таблица подключений
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS connections
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               client_id
                               INTEGER
                               NOT
                               NULL,
                               service_id
                               INTEGER
                               NOT
                               NULL,
                               start_date
                               DATE
                               NOT
                               NULL,
                               end_date
                               DATE,
                               status
                               TEXT
                               DEFAULT
                               'active',
                               FOREIGN
                               KEY
                           (
                               client_id
                           ) REFERENCES clients
                           (
                               id
                           ) ON DELETE RESTRICT,
                               FOREIGN KEY
                           (
                               service_id
                           ) REFERENCES services
                           (
                               id
                           )
                             ON DELETE RESTRICT
                               )
                           ''')

            # Таблица платежей
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS payments
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               connection_id
                               INTEGER
                               NOT
                               NULL,
                               amount
                               REAL
                               NOT
                               NULL
                               CHECK
                           (
                               amount >
                               0
                           ),
                               payment_date DATE NOT NULL,
                               payment_method TEXT DEFAULT 'cash',
                               FOREIGN KEY
                           (
                               connection_id
                           ) REFERENCES connections
                           (
                               id
                           ) ON DELETE CASCADE
                               )
                           ''')

            self.commit()
            app_logger.info("Database tables created/verified", "DB")

        except sqlite3.Error as e:
            app_logger.error(f"Error creating tables: {e}", "DB", e)

    @log_query_time
    def init_default_data(self):
        """Инициализация данных по умолчанию с хешированными паролями"""
        conn, cursor = self._get_connection()
        try:
            # Проверяем, есть ли пользователи
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                # Добавляем пользователей с хешированными паролями
                users = [
                    ("admin", "admin123", "Администратор", "admin"),
                    ("viewer", "viewer123", "Просмотрщик", "viewer"),
                ]

                for username, password, full_name, role in users:
                    hashed_pwd = hash_password(password)
                    cursor.execute(
                        "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                        (username, hashed_pwd, full_name, role)
                    )
                app_logger.info("Default users created with hashed passwords", "DB")

            # Проверяем, есть ли услуги
            cursor.execute("SELECT COUNT(*) FROM services")
            if cursor.fetchone()[0] == 0:
                services = [
                    ("Интернет 100 Мбит/с", "internet", 500.0, "Безлимитный интернет 100 Мбит/с"),
                    ("Интернет 200 Мбит/с", "internet", 750.0, "Безлимитный интернет 200 Мбит/с"),
                    ("Интерактивное ТВ Базовый", "tv", 300.0, "Базовый пакет ТВ каналов"),
                    ("Интерактивное ТВ Расширенный", "tv", 550.0, "Расширенный пакет ТВ каналов"),
                    ("Домашний телефон", "phone", 250.0, "Городская телефонная связь"),
                    ("Видеонаблюдение", "security", 800.0, "Облачное видеонаблюдение")
                ]
                for service in services:
                    cursor.execute(
                        "INSERT INTO services (name, type, cost, description) VALUES (?, ?, ?, ?)",
                        service
                    )
                app_logger.info("Default services created", "DB")

            self.commit()

            # Миграция существующих паролей (если нужно)
            self._migrate_passwords_if_needed()

        except sqlite3.Error as e:
            app_logger.error(f"Error initializing data: {e}", "DB", e)

    def _migrate_passwords_if_needed(self):
        """Миграция паролей из открытого вида в хешированный"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute("SELECT id, username, password FROM users")
            users = cursor.fetchall()

            migrated = 0
            for user in users:
                password = user['password']
                # Если пароль не содержит ':' (не хеширован)
                if ':' not in password and len(password) < 100:
                    new_hash = hash_password(password)
                    cursor.execute(
                        "UPDATE users SET password = ? WHERE id = ?",
                        (new_hash, user['id'])
                    )
                    migrated += 1

            if migrated > 0:
                self.commit()
                app_logger.info(f"Migrated {migrated} plain passwords to hashed format", "DB")

        except Exception as e:
            app_logger.error(f"Password migration error: {e}", "DB", e)

    # ========== Методы для авторизации и проверки прав ==========

    @log_query_time
    def check_user_exists(self, username: str) -> bool:
        """Проверка существования пользователя по логину"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE username = ? AND is_active = 1",
                (username,)
            )
            count = cursor.fetchone()[0]
            return count > 0
        except sqlite3.Error as e:
            app_logger.error(f"Error checking user: {e}", "DB", e)
            return False

    @log_query_time
    def check_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Проверка пользователя при входе"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute(
                "SELECT * FROM users WHERE username = ? AND is_active = 1",
                (username,)
            )
            row = cursor.fetchone()

            print(f"[DEBUG] Найден пользователь: {row is not None}")  # Отладка

            if row:
                stored_password = row['password']
                print(f"[DEBUG] Хранимый пароль: {stored_password[:50]}...")  # Отладка

                # Проверяем пароль
                if verify_password(password, stored_password):
                    cursor.execute(
                        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                        (row['id'],)
                    )
                    self.commit()
                    print(f"[DEBUG] Пароль верный!")  # Отладка
                    return dict(row)
                else:
                    print(f"[DEBUG] Пароль неверный!")  # Отладка

            return None

        except sqlite3.Error as e:
            print(f"[DEBUG] Ошибка: {e}")
            return None

    @log_query_time
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Получение пользователя по логину (без пароля)"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute(
                "SELECT id, username, full_name, role, created_at, last_login FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            app_logger.error(f"Error getting user: {e}", "DB", e)
            return None

    @log_query_time
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получение всех пользователей (для администрирования)"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute(
                "SELECT id, username, full_name, role, created_at, last_login, is_active FROM users ORDER BY id"
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            app_logger.error(f"Error getting users: {e}", "DB", e)
            return []

    @log_query_time
    def add_user(self, username: str, password: str, full_name: str, role: str = "viewer") -> Optional[int]:
        """Добавление нового пользователя с хешированным паролем"""
        conn, cursor = self._get_connection()
        try:
            hashed_pwd = hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                (username, hashed_pwd, full_name, role)
            )
            self.commit()
            app_logger.audit("system", "User created", f"Username: {username}, Role: {role}")
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Пользователь с логином {username} уже существует")
        except sqlite3.Error as e:
            app_logger.error(f"Error adding user: {e}", "DB", e)
            raise Exception(f"Ошибка добавления пользователя: {e}")

    @log_query_time
    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """Обновление роли пользователя"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute(
                "UPDATE users SET role = ? WHERE id = ?",
                (new_role, user_id)
            )
            self.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            app_logger.error(f"Error updating role: {e}", "DB", e)
            return False

    @log_query_time
    def update_user_password(self, user_id: int, new_password: str) -> bool:
        """Обновление пароля пользователя"""
        conn, cursor = self._get_connection()
        try:
            hashed_pwd = hash_password(new_password)
            cursor.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (hashed_pwd, user_id)
            )
            self.commit()
            app_logger.audit("system", "Password changed", f"User ID: {user_id}")
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            app_logger.error(f"Error updating password: {e}", "DB", e)
            return False

    # ========== Методы для аудита ==========

    @log_query_time
    def log_audit(self, user_id: int, username: str, action: str, details: str, ip_address: str = "local"):
        """Запись в аудит лог"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute(
                "INSERT INTO audit_log (user_id, username, action, details, ip_address) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, action, details, ip_address)
            )
            self.commit()
        except sqlite3.Error as e:
            app_logger.error(f"Error logging audit: {e}", "DB", e)

    @log_query_time
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение аудит лога"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute(
                "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            app_logger.error(f"Error getting audit log: {e}", "DB", e)
            return []

    # ========== Методы для работы с клиентами ==========

    @log_query_time
    def get_clients(self) -> List[Dict[str, Any]]:
        """Получение всех клиентов"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute("SELECT * FROM clients ORDER BY full_name")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            app_logger.error(f"Error getting clients: {e}", "DB", e)
            return []

    @log_query_time
    def add_client(self, full_name: str, address: str, phone: str, email: str = "") -> Optional[int]:
        """Добавление нового клиента"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute(
                "INSERT INTO clients (full_name, address, phone, email) VALUES (?, ?, ?, ?)",
                (full_name, address, phone, email)
            )
            self.commit()
            app_logger.audit("system", "Client added", f"ID={cursor.lastrowid}, Name={full_name}")
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Клиент с телефоном {phone} уже существует")
        except sqlite3.Error as e:
            app_logger.error(f"Error adding client: {e}", "DB", e)
            raise Exception(f"Ошибка добавления клиента: {e}")

    @log_query_time
    def update_client(self, client_id: int, full_name: str, address: str, phone: str, email: str = "") -> bool:
        """Обновление данных клиента"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute(
                """UPDATE clients
                   SET full_name = ?,
                       address   = ?,
                       phone     = ?,
                       email     = ?
                   WHERE id = ?""",
                (full_name, address, phone, email, client_id)
            )
            self.commit()
            app_logger.audit("system", "Client updated", f"ID={client_id}")
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            raise ValueError(f"Клиент с телефоном {phone} уже существует")
        except sqlite3.Error as e:
            app_logger.error(f"Error updating client: {e}", "DB", e)
            raise Exception(f"Ошибка обновления клиента: {e}")

    @log_query_time
    def delete_client(self, client_id: int) -> bool:
        """Удаление клиента"""
        conn, cursor = self._get_connection()
        try:
            # Проверяем, есть ли у клиента активные подключения
            cursor.execute(
                "SELECT COUNT(*) FROM connections WHERE client_id = ? AND status = 'active'",
                (client_id,)
            )
            if cursor.fetchone()[0] > 0:
                raise ValueError("Невозможно удалить клиента с активными подключениями")

            cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            self.commit()
            app_logger.audit("system", "Client deleted", f"ID={client_id}")
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            app_logger.error(f"Error deleting client: {e}", "DB", e)
            raise Exception(f"Ошибка удаления клиента: {e}")

    # ========== Методы для работы с услугами ==========

    @log_query_time
    def get_services(self) -> List[Dict[str, Any]]:
        """Получение всех услуг"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute("SELECT * FROM services ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            app_logger.error(f"Error getting services: {e}", "DB", e)
            return []

    @log_query_time
    def add_service(self, name: str, service_type: str, cost: float, description: str = "") -> Optional[int]:
        """Добавление новой услуги"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute(
                "INSERT INTO services (name, type, cost, description) VALUES (?, ?, ?, ?)",
                (name, service_type, cost, description)
            )
            self.commit()
            app_logger.audit("system", "Service added", f"ID={cursor.lastrowid}, Name={name}")
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Услуга с названием {name} уже существует")
        except sqlite3.Error as e:
            app_logger.error(f"Error adding service: {e}", "DB", e)
            raise Exception(f"Ошибка добавления услуги: {e}")

    @log_query_time
    def update_service(self, service_id: int, name: str, service_type: str, cost: float, description: str = "") -> bool:
        """Обновление услуги"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute(
                """UPDATE services
                   SET name        = ?,
                       type        = ?,
                       cost        = ?,
                       description = ?
                   WHERE id = ?""",
                (name, service_type, cost, description, service_id)
            )
            self.commit()
            app_logger.audit("system", "Service updated", f"ID={service_id}")
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            raise ValueError(f"Услуга с названием {name} уже существует")
        except sqlite3.Error as e:
            app_logger.error(f"Error updating service: {e}", "DB", e)
            raise Exception(f"Ошибка обновления услуги: {e}")

    @log_query_time
    def delete_service(self, service_id: int) -> bool:
        """Удаление услуги"""
        conn, cursor = self._get_connection()
        try:
            # Проверяем, используется ли услуга в подключениях
            cursor.execute(
                "SELECT COUNT(*) FROM connections WHERE service_id = ?",
                (service_id,)
            )
            if cursor.fetchone()[0] > 0:
                raise ValueError("Невозможно удалить услугу, которая используется в подключениях")

            cursor.execute("DELETE FROM services WHERE id = ?", (service_id,))
            self.commit()
            app_logger.audit("system", "Service deleted", f"ID={service_id}")
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            app_logger.error(f"Error deleting service: {e}", "DB", e)
            raise Exception(f"Ошибка удаления услуги: {e}")

    # ========== Методы для работы с подключениями ==========

    @log_query_time
    def get_connections(self) -> List[Dict[str, Any]]:
        """Получение всех подключений с дополнительной информацией"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute('''
                           SELECT c.*, cl.full_name as client_name, s.name as service_name, s.cost
                           FROM connections c
                                    JOIN clients cl ON c.client_id = cl.id
                                    JOIN services s ON c.service_id = s.id
                           ORDER BY c.start_date DESC
                           ''')
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            app_logger.error(f"Error getting connections: {e}", "DB", e)
            return []

    @log_query_time
    def get_connections_filtered(self, client_name: str = "", phone: str = "") -> List[Dict[str, Any]]:
        """Получение подключений с фильтрацией"""
        conn, cursor = self._get_connection()
        try:
            query = '''
                    SELECT c.*, cl.full_name as client_name, s.name as service_name, s.cost
                    FROM connections c
                             JOIN clients cl ON c.client_id = cl.id
                             JOIN services s ON c.service_id = s.id
                    WHERE 1 = 1 \
                    '''
            params = []

            if client_name:
                query += " AND cl.full_name LIKE ?"
                params.append(f"%{client_name}%")

            if phone:
                query += " AND cl.phone LIKE ?"
                params.append(f"%{phone}%")

            query += " ORDER BY c.start_date DESC"

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            app_logger.error(f"Error getting filtered connections: {e}", "DB", e)
            return []

    @log_query_time
    def add_connection(self, client_id: int, service_id: int, start_date: str, end_date: str = None) -> Optional[int]:
        """Добавление нового подключения"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute(
                "INSERT INTO connections (client_id, service_id, start_date, end_date) VALUES (?, ?, ?, ?)",
                (client_id, service_id, start_date, end_date)
            )
            self.commit()
            app_logger.audit("system", "Connection added", f"ClientID={client_id}, ServiceID={service_id}")
            return cursor.lastrowid
        except sqlite3.Error as e:
            app_logger.error(f"Error adding connection: {e}", "DB", e)
            raise Exception(f"Ошибка добавления подключения: {e}")

    @log_query_time
    def update_connection(self, connection_id: int, client_id: int, service_id: int,
                          start_date: str, end_date: str = None, status: str = "active") -> bool:
        """Обновление подключения"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute(
                """UPDATE connections
                   SET client_id  = ?,
                       service_id = ?,
                       start_date = ?,
                       end_date   = ?,
                       status     = ?
                   WHERE id = ?""",
                (client_id, service_id, start_date, end_date, status, connection_id)
            )
            self.commit()
            app_logger.audit("system", "Connection updated", f"ID={connection_id}")
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            app_logger.error(f"Error updating connection: {e}", "DB", e)
            raise Exception(f"Ошибка обновления подключения: {e}")

    @log_query_time
    def delete_connection(self, connection_id: int) -> bool:
        """Удаление подключения"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute("DELETE FROM connections WHERE id = ?", (connection_id,))
            self.commit()
            app_logger.audit("system", "Connection deleted", f"ID={connection_id}")
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            app_logger.error(f"Error deleting connection: {e}", "DB", e)
            raise Exception(f"Ошибка удаления подключения: {e}")

    # ========== Методы для работы с платежами ==========

    @log_query_time
    def get_payments(self, connection_id: int = None) -> List[Dict[str, Any]]:
        """Получение платежей (всех или по подключению)"""
        conn, cursor = self._get_connection()
        try:
            if connection_id:
                cursor.execute('''
                               SELECT p.*, cl.full_name as client_name, s.name as service_name
                               FROM payments p
                                        JOIN connections c ON p.connection_id = c.id
                                        JOIN clients cl ON c.client_id = cl.id
                                        JOIN services s ON c.service_id = s.id
                               WHERE p.connection_id = ?
                               ORDER BY p.payment_date DESC
                               ''', (connection_id,))
            else:
                cursor.execute('''
                               SELECT p.*, cl.full_name as client_name, s.name as service_name
                               FROM payments p
                                        JOIN connections c ON p.connection_id = c.id
                                        JOIN clients cl ON c.client_id = cl.id
                                        JOIN services s ON c.service_id = s.id
                               ORDER BY p.payment_date DESC
                               ''')
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            app_logger.error(f"Error getting payments: {e}", "DB", e)
            return []

    @log_query_time
    def add_payment(self, connection_id: int, amount: float, payment_date: str, method: str = "cash") -> Optional[int]:
        """Добавление платежа"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute(
                "INSERT INTO payments (connection_id, amount, payment_date, payment_method) VALUES (?, ?, ?, ?)",
                (connection_id, amount, payment_date, method)
            )
            self.commit()
            app_logger.audit("system", "Payment added", f"ConnectionID={connection_id}, Amount={amount}")
            return cursor.lastrowid
        except sqlite3.Error as e:
            app_logger.error(f"Error adding payment: {e}", "DB", e)
            raise Exception(f"Ошибка добавления платежа: {e}")

    @log_query_time
    def update_payment(self, payment_id: int, amount: float, payment_date: str, method: str,
                       connection_id: int = None) -> bool:
        """Обновление платежа"""
        conn, cursor = self._get_connection()
        try:
            if connection_id:
                cursor.execute(
                    "UPDATE payments SET amount = ?, payment_date = ?, payment_method = ?, connection_id = ? WHERE id = ?",
                    (amount, payment_date, method, connection_id, payment_id)
                )
            else:
                cursor.execute(
                    "UPDATE payments SET amount = ?, payment_date = ?, payment_method = ? WHERE id = ?",
                    (amount, payment_date, method, payment_id)
                )
            self.commit()
            app_logger.audit("system", "Payment updated", f"ID={payment_id}")
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            app_logger.error(f"Error updating payment: {e}", "DB", e)
            raise Exception(f"Ошибка обновления платежа: {e}")

    @log_query_time
    def delete_payment(self, payment_id: int) -> bool:
        """Удаление платежа"""
        conn, cursor = self._get_connection()
        try:
            cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
            self.commit()
            app_logger.audit("system", "Payment deleted", f"ID={payment_id}")
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            app_logger.error(f"Error deleting payment: {e}", "DB", e)
            raise Exception(f"Ошибка удаления платежа: {e}")

    # ========== Статистика ==========

    @log_query_time
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        conn, cursor = self._get_connection()
        try:
            stats = {}

            # Количество клиентов
            cursor.execute("SELECT COUNT(*) FROM clients")
            stats["total_clients"] = cursor.fetchone()[0]

            # Количество активных подключений
            cursor.execute("SELECT COUNT(*) FROM connections WHERE status = 'active'")
            stats["active_connections"] = cursor.fetchone()[0]

            # Общая сумма платежей
            cursor.execute("SELECT SUM(amount) FROM payments")
            stats["total_payments"] = cursor.fetchone()[0] or 0

            # Платежи за текущий месяц
            current_month = datetime.now().strftime("%Y-%m")
            cursor.execute(
                "SELECT SUM(amount) FROM payments WHERE strftime('%Y-%m', payment_date) = ?",
                (current_month,)
            )
            stats["month_payments"] = cursor.fetchone()[0] or 0

            # Записываем метрики в лог
            for table, count in [("clients", stats["total_clients"]),
                                 ("services", len(self.get_services())),
                                 ("connections", len(self.get_connections())),
                                 ("payments", len(self.get_payments()))]:
                app_logger.log_metrics(table, count)

            return stats
        except sqlite3.Error as e:
            app_logger.error(f"Error getting statistics: {e}", "DB", e)
            return {
                "total_clients": 0,
                "active_connections": 0,
                "total_payments": 0,
                "month_payments": 0
            }