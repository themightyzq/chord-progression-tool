@echo off
echo Installing dependencies for Windows...

REM Check if Python is installed
where python >nul 2>nul
if errorlevel 1 (
    echo Python not found. Please install Python 3.9+ from https://www.python.org/
    exit /b
)

REM Create and activate virtual environment
python -m venv venv
call venv\Scripts\activate

REM Upgrade pip and install Python dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

echo Setup complete. To start the tool:
echo call venv\Scripts\activate && python main.py
pause