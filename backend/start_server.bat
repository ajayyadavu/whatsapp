@echo off
REM start_server.bat — Production startup script for Swaran AI
REM Run this as Administrator or via NSSM service

cd /d D:\workbench

REM Activate virtual environment
call env\Scripts\activate.bat

REM Set environment
set PYTHONPATH=D:\workbench

REM Start uvicorn with:
REM   --workers 2        → 2 processes so one slow Ollama call doesn't block others
REM   --timeout-keep-alive 300 → match Ollama's 300s timeout
REM   --log-level info   → production logging
REM   NO --reload        → never use in production

python -m uvicorn app.main:app ^
    --host 0.0.0.0 ^
    --port 8000 ^
    --workers 2 ^
    --timeout-keep-alive 300 ^
    --log-level info
