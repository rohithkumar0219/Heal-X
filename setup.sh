#!/bin/bash

echo "================================================"
echo "Multimodal AI Healthcare Assistant - Setup"
echo "================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "[1/6] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

echo "[2/6] Activating virtual environment..."
source venv/bin/activate

echo "[3/6] Upgrading pip..."
python -m pip install --upgrade pip

echo "[4/6] Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "[5/6] Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "================================================"
    echo "IMPORTANT: Please edit .env file and add your OpenAI API key"
    echo "================================================"
    echo ""
else
    echo ".env file already exists, skipping..."
fi

echo "[6/6] Creating necessary directories..."
mkdir -p backend/static/audio
mkdir -p logs
mkdir -p temp_uploads

echo ""
echo "================================================"
echo "Setup completed successfully!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OPENAI_API_KEY"
echo "2. Run: source venv/bin/activate"
echo "3. Run: cd backend && python main.py"
echo "4. Open browser: http://localhost:8000"
echo ""
echo "For API documentation: http://localhost:8000/api/docs"
echo "================================================"
