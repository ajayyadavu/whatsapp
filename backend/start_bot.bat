@echo off
title Swaran Bot - Auto Deploy

echo ========================================
echo   Swaran WhatsApp Bot - Starting...
echo ========================================

:: Backend folder mein jaao
cd C:\Users\fresh\Desktop\whatsapp\backend

:: Step 1 - Git Pull
echo.
echo [1/5] Pulling latest code from GitHub...
git pull origin main
echo Done!

:: Step 2 - Virtual environment check karo
echo.
echo [2/5] Checking virtual environment...
if not exist "env\Scripts\activate.bat" (
    echo Creating virtual environment with Python 3.10...
    py -3.10 -m venv env
    echo Virtual environment created!
) else (
    echo Virtual environment already exists!
)
echo Done!

:: Step 3 - Dependencies install karo (venv ke andar)
echo.
echo [3/5] Installing dependencies in virtual environment...
call env\Scripts\activate.bat
pip install -r requirements.txt --quiet
echo Done!

:: Step 4 - Backend start karo (venv ke saath)
echo.
echo [4/5] Starting Backend...
start "Backend Server" cmd /k "cd C:\Users\fresh\Desktop\whatsapp\backend && call env\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 5 /nobreak >nul
echo Done!

:: Step 5 - Cloudflare Tunnel start karo
echo.
echo [5/5] Starting Cloudflare Tunnel...
start "Cloudflare Tunnel" cmd /k "C:\Users\fresh\Desktop\cloudflared-windows-amd64.exe tunnel --url http://localhost:8000"
echo Done!

echo.
echo ========================================
echo   Bot is LIVE! Check Cloudflare window
echo   for your public URL.
echo ========================================
echo.
pause
