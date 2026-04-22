@echo off
title Swaran Bot - CI/CD Restart

echo ========================================
echo   Swaran Bot - Auto Restarting...
echo ========================================

:: Purane processes band karo
taskkill /F /FI "WINDOWTITLE eq Backend Server*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Swaran*" >nul 2>&1
timeout /t 3 /nobreak >nul

:: Latest code pull karo
cd C:\Users\fresh\Desktop\whatsapp\backend
git pull origin main

:: Dependencies update karo
call env\Scripts\activate.bat
pip install -r requirements.txt --quiet

:: Server start karo
start "Backend Server" cmd /k "cd C:\Users\fresh\Desktop\whatsapp\backend && call env\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 5 /nobreak >nul

echo ========================================
echo   Bot Restarted Successfully!
echo ========================================
