@echo off
title Geography AI - Start

echo ============================================
echo    Geography AI Assistant
echo    Backend : http://localhost:8000
echo    Frontend: http://localhost:5173
echo ============================================

REM --- Start Backend ---
start "Backend" cmd /k "cd /d D:\Learn\claude_project\Geography-1.0\backend && venv\Scripts\python.exe main.py"

REM --- Wait for backend ---
echo Waiting for backend...
timeout /t 5 /nobreak >nul

REM --- Start Frontend ---
start "Frontend" cmd /k "cd /d D:\Learn\claude_project\Geography-1.0\frontend && npm run dev"

echo.
echo Both services started!
echo Open http://localhost:5173
echo.

timeout /t 2 /nobreak >nul
start http://localhost:5173
pause
