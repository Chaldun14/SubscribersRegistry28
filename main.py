# main.py (обновленная версия)
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Реестр подключенных услуг
Версия: 2026.1.0
Разработчик: Волобоев Максим Александрович
Группа: ИС-22
"""

import sys
import os
import traceback
import atexit


# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_manager import config_manager
from logger import app_logger
from backup_manager import BackupManager


def cleanup():
    """Очистка при выходе"""
    try:
        import threading
        for thread in threading.enumerate():
            if thread.name != "MainThread":
                try:
                    pass
                except:
                    pass
    except:
        pass


def check_dependencies():
    """Проверка наличия необходимых модулей"""
    required_modules = [
        ('customtkinter', 'customtkinter'),
        ('PIL', 'Pillow'),
        ('pystray', 'pystray'),
        ('plyer', 'plyer')
    ]

    missing_modules = []

    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
        except ImportError:
            missing_modules.append(package_name)

    return missing_modules


def create_assets_folder():
    """Создание папки assets с тестовым PDF"""
    if not os.path.exists("assets"):
        os.makedirs("assets")
        print("📁 Создана папка assets")

    # Создаем папку для бэкапов
    if not os.path.exists("backups"):
        os.makedirs("backups")
        print("📁 Создана папка backups")

    # Создаем папку для логов
    if not os.path.exists("logs"):
        os.makedirs("logs")
        print("📁 Создана папка logs")

    # Создаем тестовый PDF файл, если его нет
    pdf_path = "user_manual.pdf"
    if not os.path.exists(pdf_path):
        try:
            with open(pdf_path, "wb") as f:
                f.write(
                    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF")
            print(f"📄 Создан тестовый файл руководства: {pdf_path}")
        except Exception as e:
            print(f"⚠️ Не удалось создать тестовый PDF: {e}")


def ensure_users_exist():
    """Проверка и создание пользователей если их нет"""
    from database import Database
    from password_hasher import hash_password

    db = Database()
    try:
        conn, cursor = db._get_connection()

        # Проверяем, есть ли пользователи
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]

        if count == 0:
            print("👤 Создание пользователей по умолчанию...")

            # Создаем администратора
            admin_hash = hash_password("admin123")
            cursor.execute(
                "INSERT INTO users (username, password, full_name, role, is_active) VALUES (?, ?, ?, ?, ?)",
                ("admin", admin_hash, "Администратор", "admin", 1)
            )

            # Создаем гостя
            guest_hash = hash_password("guest123")
            cursor.execute(
                "INSERT INTO users (username, password, full_name, role, is_active) VALUES (?, ?, ?, ?, ?)",
                ("guest", guest_hash, "Гость", "viewer", 1)
            )

            db.commit()
            print("✅ Пользователи созданы: admin/admin123, guest/guest123")

        # Проверяем, есть ли услуги
        cursor.execute("SELECT COUNT(*) FROM services")
        services_count = cursor.fetchone()[0]

        if services_count == 0:
            print("📦 Создание услуг по умолчанию...")
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
            db.commit()
            print("✅ Услуги созданы")

    except Exception as e:
        print(f"❌ Ошибка при создании пользователей: {e}")
    finally:
        db.close()


def main():
    """Главная функция приложения"""
    atexit.register(cleanup)

    try:
        print("🚀 Запуск программы 'Реестр подключенных услуг'")
        print("-" * 50)

        # Загрузка конфигурации
        config = config_manager
        current_theme = config.get("theme", "light")
        print(f"🎨 Тема: {current_theme}")

        # Валидация конфигурации
        validation = config.validate()
        if validation["warnings"]:
            for warning in validation["warnings"]:
                print(f"⚠️ Предупреждение: {warning}")
        if validation["errors"]:
            for error in validation["errors"]:
                print(f"❌ Ошибка: {error}")

        # Проверка зависимостей
        missing = check_dependencies()
        if missing:
            print("❌ Отсутствуют необходимые модули:")
            for module in missing:
                print(f"   - {module}")
            print("\n📦 Установите их командой:")
            print(f"   pip install {' '.join(missing)}")
            input("\nНажмите Enter для выхода...")
            return 1

        # Создание необходимых папок
        create_assets_folder()

        # ПРОВЕРКА И СОЗДАНИЕ ПОЛЬЗОВАТЕЛЕЙ
        ensure_users_exist()

        # Импортируем модули приложения
        print("📚 Загрузка модулей приложения...")
        from ui.styles import AppStyles
        from ui.login_window import LoginWindow
        from ui.main_window import MainWindow
        from database import Database

        print("🎨 Настройка темы...")
        AppStyles.apply_theme(current_theme)

        print("🔐 Запуск окна авторизации...")
        login = LoginWindow(theme=current_theme)
        success, user_data, theme_used = login.show()

        print(f"📊 Результат входа: success={success}")

        if success and user_data:
            print(f"✅ Успешный вход: {user_data['full_name']} ({user_data['role']})")
            print("🪟 Открытие главного окна...")

            # Сохраняем тему
            config.set("theme", theme_used)

            app = MainWindow(user_data, theme=theme_used)
            app.show()
        else:
            print("👋 Выход из программы")

    except KeyboardInterrupt:
        print("\n👋 Программа завершена пользователем")
        app_logger.info("Application interrupted by user", "App")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        traceback.print_exc()
        app_logger.error(f"Critical error: {e}", "App", e)
        input("\nНажмите Enter для выхода...")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())