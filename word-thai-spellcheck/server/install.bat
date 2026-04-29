@echo off
REM install.bat — ติดตั้ง Thai Spell Checker Server (Windows)

echo === Thai Spell Checker — Server Setup ===
echo.

REM ตรวจสอบ Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ไม่พบ Python กรุณาติดตั้งก่อน: https://www.python.org
    pause
    exit /b 1
)
echo [OK] Python พบแล้ว

REM ตรวจสอบ Ollama
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ไม่พบ Ollama กรุณาติดตั้งก่อน: https://ollama.ai
    pause
    exit /b 1
)
echo [OK] Ollama พบแล้ว

REM สร้าง virtual environment
cd /d "%~dp0"
echo.
echo [INFO] สร้าง virtual environment...
python -m venv venv

echo [INFO] ติดตั้ง dependencies...
call venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

echo.
echo [OK] ติดตั้งเสร็จแล้ว!
echo.
echo วิธีรัน server:
echo   cd %~dp0
echo   venv\Scripts\activate.bat
echo   python main.py
echo.
pause
