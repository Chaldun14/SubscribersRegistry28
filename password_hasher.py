# password_hasher.py
import hashlib
import os
import base64
from typing import Tuple
import secrets


class PasswordHasher:
    """Класс для хеширования паролей с использованием SHA-256 и соли"""

    ITERATIONS = 100000

    @staticmethod
    def generate_salt(length: int = 32) -> str:
        """Генерация случайной соли"""
        return base64.b64encode(secrets.token_bytes(length)).decode('utf-8')

    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        """Хеширование пароля с солью"""
        if salt is None:
            salt = PasswordHasher.generate_salt()

        # Комбинируем пароль и соль
        salted_password = (password + salt).encode('utf-8')

        # Применяем SHA-256 с множеством итераций
        hash_value = salted_password
        for _ in range(PasswordHasher.ITERATIONS):
            hash_value = hashlib.sha256(hash_value).digest()

        # Кодируем в base64 для хранения
        password_hash = base64.b64encode(hash_value).decode('utf-8')

        return password_hash, salt

    @staticmethod
    def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
        """Проверка пароля"""
        computed_hash, _ = PasswordHasher.hash_password(password, stored_salt)
        return computed_hash == stored_hash


# Простые функции для обратной совместимости
def hash_password(password: str) -> str:
    """Упрощенная функция хеширования"""
    pwd_hash, salt = PasswordHasher.hash_password(password)
    result = f"{pwd_hash}:{salt}"
    print(f"[DEBUG] Хеширование пароля: {password} -> {result[:50]}...")  # Отладка
    return result


def verify_password(password: str, stored: str) -> bool:
    """Упрощенная функция проверки"""
    print(f"[DEBUG] Проверка пароля: {password} против {stored[:50]}...")  # Отладка

    # Если пароль не в формате "hash:salt" (старый формат)
    if ':' not in stored:
        print(f"[DEBUG] Старый формат пароля (открытый текст): {stored == password}")
        return password == stored

    try:
        pwd_hash, salt = stored.split(':', 1)
        result = PasswordHasher.verify_password(password, pwd_hash, salt)
        print(f"[DEBUG] Результат проверки: {result}")
        return result
    except Exception as e:
        print(f"[DEBUG] Ошибка проверки пароля: {e}")
        return False