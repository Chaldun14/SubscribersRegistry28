import json
import os


class Config:
    """Класс для работы с конфигурацией"""

    CONFIG_FILE = "config.json"

    @classmethod
    def load(cls):
        """Загрузка конфигурации"""
        default_config = {
            "theme": "light",
            "window": {
                "width": 1200,
                "height": 700
            }
        }

        try:
            if os.path.exists(cls.CONFIG_FILE):
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Проверяем наличие всех ключей
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                    return config
            else:
                return default_config
        except:
            return default_config

    @classmethod
    def save(cls, config):
        """Сохранение конфигурации"""
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")