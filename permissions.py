# permissions.py (обновленная версия)
from typing import List, Dict, Any


class Permissions:
    """Класс для проверки прав доступа на основе роли пользователя"""

    # Определение прав для каждой роли
    ROLE_PERMISSIONS = {
        "admin": {  # Администратор - полный доступ
            "can_view_all": True,
            "can_add": True,
            "can_edit": True,
            "can_delete": True,
            "can_import": True,
            "can_export": True,
            "can_manage_users": True,
            "can_view_statistics": True,
            "can_access_tray": True,
            "can_search": True,
            "can_backup": True,
            "can_settings": True,
        },
        "viewer": {  # Просмотрщик - только чтение
            "can_view_all": True,
            "can_add": False,
            "can_edit": False,
            "can_delete": False,
            "can_import": False,
            "can_export": False,
            "can_manage_users": False,
            "can_view_statistics": False,
            "can_access_tray": True,
            "can_search": True,
            "can_backup": False,
            "can_settings": True,  # Может менять свои настройки (тему, масштаб)
        }
    }

    @classmethod
    def has_permission(cls, user_role: str, permission: str) -> bool:
        """Проверка наличия права у пользователя"""
        if user_role not in cls.ROLE_PERMISSIONS:
            return False
        return cls.ROLE_PERMISSIONS[user_role].get(permission, False)

    @classmethod
    def get_allowed_actions(cls, user_role: str) -> List[str]:
        """Получение списка разрешенных действий для роли"""
        if user_role not in cls.ROLE_PERMISSIONS:
            return []
        return [action for action, allowed in cls.ROLE_PERMISSIONS[user_role].items() if allowed]

    @classmethod
    def get_role_description(cls, user_role: str) -> str:
        """Получение описания роли"""
        descriptions = {
            "admin": "Полный доступ ко всем функциям (администратор)",
            "viewer": "Только просмотр данных (без возможности редактирования)"
        }
        return descriptions.get(user_role, "Неизвестная роль")

    @classmethod
    def get_available_roles(cls) -> List[Dict[str, str]]:
        """Получение списка доступных ролей"""
        return [
            {"name": "admin", "description": "Администратор - полный доступ"},
            {"name": "viewer", "description": "Просмотрщик - только чтение"}
        ]

    @classmethod
    def can_user_perform_action(cls, user_role: str, action: str,
                                current_user_role: str = None) -> bool:
        """
        Проверка возможности выполнения действия с учетом роли текущего пользователя

        Args:
            user_role: Роль пользователя, над которым выполняется действие
            action: Действие (например, "change_role")
            current_user_role: Роль текущего пользователя
        """
        # Только администратор может менять роли других пользователей
        if action == "change_role":
            return current_user_role == "admin"

        # Администратор не может удалить сам себя (защита)
        if action == "delete_self" and user_role == "admin":
            return False

        return cls.has_permission(current_user_role or user_role, action)