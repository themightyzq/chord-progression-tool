@echo off
echo Installing dependencies for Windows...
echo.
echo If this window closes immediately, please run this script from an open Command Prompt window for better error visibility.
echo.

REM Check if Python is installed
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b
)

REM Check if Chocolatey is installed
where choco >nul 2>nul
if errorlevel 1 (
    echo [INFO] Chocolatey not found. PortAudio must be installed manually.
    echo.
    echo Download PortAudio from:
    echo   https://www.portaudio.com/download.html
    echo.
    echo Place 'portaudio_x64.dll' or 'portaudio.dll' in one of the following:
    echo   - This project folder
    echo   - venv\Scripts
    echo   - Any folder in your system PATH
) else (
    echo [INFO] Chocolatey found, but PortAudio must still be installed manually.
    echo Download and install from:
    echo   https://www.portaudio.com/download.html
)

REM Create virtual environment
echo.
echo Creating Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Upgrade pip and install requirements
echo Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ===============================
echo Setup complete!
echo ===============================
echo.
echo IMPORTANT: Make sure PortAudio DLL is placed correctly for audio playback.
echo Run the app using:
echo   call venv\Scripts\activate && python main.py
pause
