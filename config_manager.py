# config_manager.py
import json
import os
import shutil
from typing import Dict, Any, Optional
from datetime import datetime


class ConfigManager:
    """Менеджер конфигурации приложения"""

    CONFIG_FILE = "config.json"
    BACKUP_CONFIG_FILE = "config_backup.json"

    # Значения по умолчанию
    DEFAULT_CONFIG = {
        "theme": "light",
        "scale": 1.0,
        "font_family": "Segoe UI",
        "window": {
            "width": 1400,  # Было 1300
            "height": 800  # Было 700
        },
        "backup": {
            "enabled": True,
            "interval_value": 1,
            "interval_unit": "days",
            "max_backups": 10
        },
        "notifications": {
            "sound_enabled": True,
            "dialogs_enabled": True,
            "tray_notifications": True
        },
        "hotkeys_enabled": True,
        "tips_enabled": True,
        "log_level": "INFO",
        "auto_cleanup_days": 30
    }

    # Доступные масштабы
    AVAILABLE_SCALES = {
        "75%": 0.75,
        "100%": 1.0,
        "125%": 1.25,
        "150%": 1.5
    }

    # Доступные шрифты
    AVAILABLE_FONTS = ["Segoe UI", "Arial", "Times New Roman", "Calibri", "Verdana"]

    # Единицы времени для автобэкапа
    TIME_UNITS = {
        "minutes": "минут",
        "hours": "часов",
        "days": "дней"
    }

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Загрузка конфигурации из файла"""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Рекурсивное обновление с дефолтными значениями
                    self._config = self._merge_configs(self.DEFAULT_CONFIG.copy(), loaded_config)
            else:
                self._config = self.DEFAULT_CONFIG.copy()
                self._save()
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            self._config = self.DEFAULT_CONFIG.copy()

    def _merge_configs(self, default: Dict, custom: Dict) -> Dict:
        """Рекурсивное слияние конфигураций"""
        result = default.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def _save(self) -> bool:
        """Сохранение конфигурации в файл"""
        try:
            # Создаем резервную копию перед сохранением
            if os.path.exists(self.CONFIG_FILE):
                shutil.copy2(self.CONFIG_FILE, self.BACKUP_CONFIG_FILE)

            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения по ключу (поддерживает точечную нотацию)"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> bool:
        """Установка значения по ключу (поддерживает точечную нотацию)"""
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        return self._save()

    def validate(self) -> Dict[str, Any]:
        """Валидация конфигурации"""
        errors = []
        warnings = []

        # Проверка темы
        if self.get("theme") not in ["light", "dark"]:
            errors.append(f"Некорректное значение theme: {self.get('theme')}")
            self.set("theme", "light")

        # Проверка масштаба
        scale = self.get("scale")
        if scale not in list(self.AVAILABLE_SCALES.values()):
            warnings.append(f"Масштаб {scale} не в списке доступных, используется 1.0")
            self.set("scale", 1.0)

        # Проверка шрифта
        font = self.get("font_family")
        if font not in self.AVAILABLE_FONTS:
            warnings.append(f"Шрифт {font} не в списке доступных, используется Segoe UI")
            self.set("font_family", "Segoe UI")

        # Проверка интервала бэкапа
        backup_interval = self.get("backup.interval_value", 1)
        if backup_interval < 1:
            errors.append("Интервал бэкапа должен быть больше 0")
            self.set("backup.interval_value", 1)

        # Проверка максимального количества бэкапов
        max_backups = self.get("backup.max_backups", 10)
        if max_backups < 1:
            errors.append("Максимальное количество бэкапов должно быть больше 0")
            self.set("backup.max_backups", 10)

        # Проверка автоочистки
        auto_cleanup = self.get("auto_cleanup_days", 30)
        if auto_cleanup < 1:
            warnings.append("Автоочистка должна быть больше 0 дней, установлено 30")
            self.set("auto_cleanup_days", 30)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def reset_to_defaults(self) -> bool:
        """Сброс к настройкам по умолчанию"""
        self._config = self.DEFAULT_CONFIG.copy()
        return self._save()

    def get_scale_percent(self) -> str:
        """Получение масштаба в процентах для отображения"""
        scale = self.get("scale", 1.0)
        for percent, value in self.AVAILABLE_SCALES.items():
            if value == scale:
                return percent
        return "100%"

    def set_scale_by_percent(self, percent: str) -> bool:
        """Установка масштаба по проценту"""
        if percent in self.AVAILABLE_SCALES:
            return self.set("scale", self.AVAILABLE_SCALES[percent])
        return False

    def get_backup_interval_seconds(self) -> int:
        """Получение интервала бэкапа в секундах"""
        interval = self.get("backup.interval_value", 1)
        unit = self.get("backup.interval_unit", "days")

        if unit == "minutes":
            return interval * 60
        elif unit == "hours":
            return interval * 3600
        else:  # days
            return interval * 86400

    def get_backup_interval_display(self) -> str:
        """Получение интервала бэкапа для отображения"""
        interval = self.get("backup.interval_value", 1)
        unit = self.get("backup.interval_unit", "days")
        unit_display = self.TIME_UNITS.get(unit, "дней")

        # Склонение
        if interval == 1:
            if unit == "minutes":
                unit_display = "минуту"
            elif unit == "hours":
                unit_display = "час"
            else:
                unit_display = "день"
        elif interval in [2, 3, 4]:
            if unit == "minutes":
                unit_display = "минуты"
            elif unit == "hours":
                unit_display = "часа"
            else:
                unit_display = "дня"

        return f"{interval} {unit_display}"

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def are_tips_enabled(self) -> bool:
        """Проверка, включены ли подсказки"""
        return self.get("tips_enabled", True)



# Глобальный экземпляр для использования во всем приложении
config_manager = ConfigManager()