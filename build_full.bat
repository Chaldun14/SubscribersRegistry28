@echo off
chcp 65001 > nul
title ПОЛНАЯ СБОРКА ПРОГРАММЫ
echo ========================================
echo    ПОЛНАЯ СБОРКА ПРОГРАММЫ
echo ========================================
echo.

cd /d "E:\ПП 04.01\SubscribersRegistry"

echo [1/6] Активация виртуального окружения...
call .venv\Scripts\activate

echo [2/6] Очистка предыдущих сборок...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q installer 2>nul
del *.spec 2>nul

echo [3/6] Сборка .exe файла...
echo.

pyinstaller --onefile --windowed ^
    --icon=assets/icon.ico ^
    --add-data "assets;assets" ^
    --add-data "config.json;." ^
    --add-data "user_manual_admin.pdf;assets" ^
    --add-data "user_manual_guest.pdf;assets" ^
    --hidden-import customtkinter ^
    --hidden-import PIL ^
    --hidden-import PIL._tkinter_finder ^
    --hidden-import pystray ^
    --hidden-import plyer ^
    --hidden-import sqlite3 ^
    --hidden-import datetime ^
    --hidden-import json ^
    --hidden-import xml.etree.ElementTree ^
    --hidden-import threading ^
    --hidden-import tkinter ^
    --hidden-import darkdetect ^
    --hidden-import reportlab ^
    --name "SubscribersRegistry" ^
    main.py

if %errorlevel% neq 0 (
    echo [❌] Ошибка при сборке .exe
    pause
    exit /b 1
)

echo.
echo [4/6] Копирование дополнительных файлов...
if not exist "dist\assets" mkdir "dist\assets"
xcopy /E /I /Y assets dist\assets > nul
copy config.json dist\ > nul 2>&1
copy user_manual_admin.pdf dist\assets\ > nul 2>&1
copy user_manual_guest.pdf dist\assets\ > nul 2>&1
copy README.txt dist\ > nul 2>&1
copy LICENSE.txt dist\ > nul 2>&1
if exist subscribers.db copy subscribers.db dist\ > nul 2>&1

echo.
echo [5/6] Создание установщика...

REM Проверка наличия Inno Setup
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    "C:\Program Files\Inno Setup 6\ISCC.exe" installer.iss
) else if exist "C:\Program Files (x86)\Inno Setup\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup\ISCC.exe" installer.iss
) else (
    echo.
    echo [⚠️] Inno Setup не найден.
    echo      Установите Inno Setup с сайта:
    echo      https://jrsoftware.org/isdl.php
    echo.
    echo      После установки запустите сборку установщика вручную:
    echo      "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
)

echo.
echo [6/6] Очистка временных файлов...
rmdir /s /q build 2>nul
del *.spec 2>nul

echo.
echo ========================================
echo    ГОТОВО!
echo ========================================
echo.
echo 📁 .exe файл: dist\SubscribersRegistry.exe
echo 📁 Установщик: installer\SubscribersRegistry_Setup.exe
echo.
echo Размер .exe файла:
dir dist\SubscribersRegistry.exe
echo.
if exist installer\SubscribersRegistry_Setup.exe (
    echo Размер установщика:
    dir installer\SubscribersRegistry_Setup.exe
)
echo.
pause