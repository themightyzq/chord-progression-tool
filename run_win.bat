@echo off
echo ===============================
echo Launching Chord Progression Tool...
echo ===============================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. Please run install_win.bat first.
    pause
    exit /b
)

REM Activate virtual environment
call venv\Scripts\activate

REM Run the app
python main.py

echo.
pause