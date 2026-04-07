# backup_manager.py
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import time


class BackupManager:
    BACKUP_DIR = "backups"

    def __init__(self, db_path: str = "subscribers.db"):
        self.db_path = db_path
        self._ensure_backup_dir()
        self._auto_backup_running = False

    def _ensure_backup_dir(self):
        if not os.path.exists(self.BACKUP_DIR):
            os.makedirs(self.BACKUP_DIR)

    def _enforce_max_backups(self, max_backups: int):
        """Ограничение количества бэкапов до указанного числа"""
        if max_backups <= 0:
            return

        backups = self.list_backups()
        if len(backups) > max_backups:
            backups_to_delete = backups[max_backups:]
            for backup in backups_to_delete:
                try:
                    os.remove(backup["path"])
                    print(f"Удален старый бэкап: {backup['name']}")
                except Exception as e:
                    print(f"Ошибка удаления {backup['name']}: {e}")

    def create_backup(self, callback: Optional[callable] = None, show_dialog: bool = True) -> Optional[str]:
        """
        Создание резервной копии

        Args:
            callback: Функция обратного вызова
            show_dialog: Показывать ли диалоговое окно (True - ручное создание, False - автоматическое)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.db"
            backup_path = os.path.join(self.BACKUP_DIR, backup_name)

            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"База данных не найдена: {self.db_path}")

            shutil.copy2(self.db_path, backup_path)

            if self._verify_backup(backup_path):
                from config_manager import config_manager
                max_backups = config_manager.get("backup.max_backups", 10)
                self._enforce_max_backups(max_backups)

                if callback:
                    # Передаем параметр show_dialog в callback
                    callback(True, backup_path, "Бэкап создан успешно", show_dialog)
                return backup_path
            else:
                os.remove(backup_path)
                raise Exception("Проверка целостности бэкапа не пройдена")
        except Exception as e:
            if callback:
                callback(False, None, f"Ошибка создания бэкапа: {e}", show_dialog)
            return None

    def _verify_backup(self, backup_path: str) -> bool:
        try:
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            conn.close()
            return result == "ok"
        except:
            return False

    def restore_backup(self, backup_path: str, callback: Optional[callable] = None) -> bool:
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Файл бэкапа не найден: {backup_path}")

            if not self._verify_backup(backup_path):
                raise Exception("Бэкап поврежден")

            emergency_backup = self.create_backup(show_dialog=False)
            if emergency_backup:
                print(f"Создан аварийный бэкап: {emergency_backup}")

            shutil.copy2(backup_path, self.db_path)

            if self._verify_backup(self.db_path):
                if callback:
                    callback(True, "База данных восстановлена успешно")
                return True
            else:
                raise Exception("Проверка восстановленной БД не пройдена")
        except Exception as e:
            if callback:
                callback(False, f"Ошибка восстановления: {e}")
            return False

    def list_backups(self) -> List[Dict[str, any]]:
        backups = []
        if not os.path.exists(self.BACKUP_DIR):
            return backups
        for filename in os.listdir(self.BACKUP_DIR):
            if filename.startswith("backup_") and filename.endswith(".db"):
                filepath = os.path.join(self.BACKUP_DIR, filename)
                stat = os.stat(filepath)
                try:
                    timestamp_str = filename.replace("backup_", "").replace(".db", "")
                    created = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                except:
                    created = datetime.fromtimestamp(stat.st_mtime)
                backups.append({
                    "name": filename,
                    "path": filepath,
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created": created,
                    "created_str": created.strftime("%Y-%m-%d %H:%M:%S")
                })
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups

    def cleanup_old_backups(self, days: int = 30, callback: Optional[callable] = None) -> int:
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=days)
        backups = self.list_backups()
        for backup in backups:
            if backup["created"] < cutoff_date:
                try:
                    os.remove(backup["path"])
                    deleted_count += 1
                except Exception as e:
                    print(f"Ошибка удаления {backup['name']}: {e}")
        if callback:
            callback(deleted_count, days)
        return deleted_count

    def get_backup_info(self) -> Dict[str, any]:
        backups = self.list_backups()
        total_size = sum(b["size"] for b in backups)
        return {
            "total_backups": len(backups),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "latest_backup": backups[0] if backups else None,
            "oldest_backup": backups[-1] if backups else None
        }

    def start_auto_backup(self, interval_seconds: int, callback: Optional[callable] = None):
        """Запуск автоматического резервного копирования (без диалоговых окон)"""
        if interval_seconds <= 0:
            return

        self._auto_backup_running = True
        self._auto_backup_callback = callback

        def run():
            while self._auto_backup_running:
                time.sleep(interval_seconds)
                if self._auto_backup_running:
                    # Автоматический бэкап - show_dialog=False
                    backup_path = self.create_backup(callback, show_dialog=False)
                    if backup_path and callback:
                        callback(True, backup_path, "Автоматический бэкап создан", False)

                    from config_manager import config_manager
                    cleanup_days = config_manager.get("auto_cleanup_days", 30)
                    self.cleanup_old_backups(cleanup_days)

                    max_backups = config_manager.get("backup.max_backups", 10)
                    self._enforce_max_backups(max_backups)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def stop_auto_backup(self):
        """Остановка автоматического резервного копирования"""
        self._auto_backup_running = False