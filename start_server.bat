@echo off
echo Starting Multimodal AI Healthcare Assistant...
echo.

cd /d "%~dp0"
cd backend

REM Set environment variable directly (if not using .env)
REM set OPENAI_API_KEY=your_key_here

REM Activate virtual environment
call ..\venv\Scripts\activate.bat

echo.
echo ================================================
echo Server starting on http://localhost:8000
echo API Docs: http://localhost:8000/api/docs
echo ================================================
echo.

python main.py

if errorlevel 1 (
    echo.
    echo Server crashed or failed to start.
    pause
)
