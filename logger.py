# logger.py
import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional
import traceback
import time

# Путь к папке с логами
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5


class CustomFormatter(logging.Formatter):
    """Пользовательский форматтер для логов"""

    def format(self, record):
        # Формат: [YYYY-MM-DD HH:MM:SS] [LEVEL] [Category] Message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        category = getattr(record, 'category', 'App')
        message = record.getMessage()

        return f"[{timestamp}] [{level}] [{category}] {message}"


class AppLogger:
    """Класс для логирования действий приложения"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._setup_logging()
        self._query_times = []
        self._start_time = time.time()

    def _setup_logging(self):
        """Настройка системы логирования"""
        # Создаем папку для логов если её нет
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)

        # Настраиваем корневой логгер
        self.logger = logging.getLogger("SubscribersRegistry")
        self.logger.setLevel(logging.DEBUG)

        # Очищаем существующие обработчики
        self.logger.handlers.clear()

        # Обработчик с ротацией
        handler = logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        handler.setFormatter(CustomFormatter())
        self.logger.addHandler(handler)

        # Консольный обработчик для отладки
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(CustomFormatter())
        console_handler.setLevel(logging.WARNING)
        self.logger.addHandler(console_handler)

    def _log(self, level: int, message: str, category: str = "App",
             exception: Optional[Exception] = None):
        """Внутренний метод для логирования"""
        extra = {'category': category}

        if exception:
            message += f"\n{''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))}"

        self.logger.log(level, message, extra=extra)

    def info(self, message: str, category: str = "App"):
        """Информационное сообщение"""
        self._log(logging.INFO, message, category)

    def warning(self, message: str, category: str = "App"):
        """Предупреждение"""
        self._log(logging.WARNING, message, category)

    def error(self, message: str, category: str = "App", exception: Optional[Exception] = None):
        """Ошибка с деталями"""
        self._log(logging.ERROR, message, category, exception)

    def debug(self, message: str, category: str = "App"):
        """Отладочное сообщение"""
        self._log(logging.DEBUG, message, category)

    def audit(self, user_id: str, action: str, details: str, category: str = "Security"):
        """Аудит действий пользователей"""
        message = f"[User: {user_id}] {action}: {details}"
        self._log(logging.INFO, message, category)

    def log_query_time(self, query: str, duration_ms: float):
        """Логирование времени выполнения SQL запроса"""
        if duration_ms > 1000:  # Медленный запрос > 1 секунды
            self.warning(f"Slow query detected: {duration_ms:.2f}ms - {query[:100]}", "DB")
        else:
            self.debug(f"Query executed in {duration_ms:.2f}ms - {query[:100]}", "Metrics")
        self._query_times.append(duration_ms)

    def log_metrics(self, table_name: str, record_count: int):
        """Логирование метрик (количество записей в таблице)"""
        self.info(f"Records in table {table_name}: {record_count}", "Metrics")

    def log_app_start(self):
        """Логирование запуска приложения"""
        self.info("Application started", "App")

    def log_app_close(self):
        """Логирование закрытия приложения"""
        uptime = time.time() - self._start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        self.info(f"Application closed (uptime: {hours}h {minutes}m {seconds}s)", "App")

    def log_db_connected(self, db_path: str):
        """Логирование подключения к БД"""
        self.info(f"DB connected: {db_path}", "Metrics")

    def log_user_login(self, username: str, success: bool):
        """Логирование попытки входа"""
        if success:
            self.info(f"User {username} logged in", "Security")
        else:
            self.warning(f"Failed login attempt for user {username}", "Security")

    def log_settings_change(self, username: str, setting: str, old_value: Any, new_value: Any):
        """Логирование изменения настроек"""
        self.info(f"User {username} changed {setting} from {old_value} to {new_value}", "Settings")

    def log_backup_created(self, backup_path: str):
        """Логирование создания бэкапа"""
        self.info(f"Backup created: {os.path.basename(backup_path)}", "Backup")

    def log_backup_restored(self, backup_path: str):
        """Логирование восстановления из бэкапа"""
        self.info(f"Backup restored: {os.path.basename(backup_path)}", "Backup")

    def log_backup_cleanup(self, deleted_count: int, days: int):
        """Логирование очистки старых бэкапов"""
        self.info(f"Cleaned up {deleted_count} old backups (older than {days} days)", "Backup")

    def log_permission_denied(self, username: str, action: str):
        """Логирование отказа в доступе"""
        self.warning(f"Permission denied for user {username} to perform {action}", "Security")

    def log_unauthorized_access(self, username: str, action: str, ip: str = "local"):
        """Логирование несанкционированного доступа"""
        self.error(f"UNAUTHORIZED ACCESS: User {username} attempted {action}", "Security")


# Глобальный экземпляр
app_logger = AppLogger()


# Декоратор для замера времени выполнения SQL запросов
def log_query_time(func):
    """Декоратор для замера времени выполнения SQL запросов"""

    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        try:
            result = func(self, *args, **kwargs)
            duration = (time.time() - start_time) * 1000
            app_logger.log_query_time(func.__name__, duration)
            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            app_logger.log_query_time(func.__name__, duration)
            app_logger.error(f"Query failed: {func.__name__}", "DB", e)
            raise

    return wrapper