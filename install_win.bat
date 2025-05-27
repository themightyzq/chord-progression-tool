@echo off
echo ===============================
echo Installing Chord Progression Tool (Windows)
echo ===============================
echo.

REM Check if Python is installed
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b
)

REM Activate virtual environment
call venv\Scripts\activate

REM Upgrade pip and install dependencies
echo Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Optional: verify sounddevice loads
python -c "import sounddevice; print('[INFO] sounddevice loaded:', sounddevice.query_devices())" || (
    echo [WARNING] sounddevice could not be initialized. Please check your audio configuration.
)

echo.
echo ===============================
echo Setup complete!
echo ===============================
echo To run the tool:
echo   call venv\Scripts\activate && python main.py
pause
