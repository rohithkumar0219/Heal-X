@echo off
echo ================================================
echo Multimodal AI Healthcare Assistant - Setup
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo [1/6] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/6] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/6] Upgrading pip...
python -m pip install --upgrade pip

echo [4/6] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [5/6] Creating .env file...
if not exist .env (
    copy .env.example .env
    echo.
    echo ================================================
    echo IMPORTANT: Please edit .env file and add your OpenAI API key
    echo ================================================
    echo.
) else (
    echo .env file already exists, skipping...
)

echo [6/6] Creating necessary directories...
if not exist backend\static\audio mkdir backend\static\audio
if not exist logs mkdir logs
if not exist temp_uploads mkdir temp_uploads

echo.
echo ================================================
echo Setup completed successfully!
echo ================================================
echo.
echo Next steps:
echo 1. Edit .env file and add your OPENAI_API_KEY
echo 2. Run: cd backend
echo 3. Run: python main.py
echo 4. Open browser: http://localhost:8000
echo.
echo For API documentation: http://localhost:8000/api/docs
echo ================================================
pause
