@echo off
REM Start script for mBot IoT Gateway (Windows)

echo Starting mBot IoT Gateway...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Create data directory if it doesn't exist
if not exist "data" mkdir data

echo.
echo Starting Flask server...
echo Dashboard will be available at: http://localhost:5000
echo API endpoints at: http://localhost:5000/api/*
echo.
echo Press Ctrl+C to stop the server
echo.

cd backend
python app.py

pause
