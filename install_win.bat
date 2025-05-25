@echo off
echo Installing dependencies for Windows...

REM Check if Python is installed
where python >nul 2>nul
if errorlevel 1 (
    echo Python not found. Please install Python 3.9+ from https://www.python.org/
    exit /b
)

REM Check if Chocolatey is installed
where choco >nul 2>nul
if errorlevel 1 (
    echo Chocolatey not found. Please install PortAudio manually from http://www.portaudio.com/download.html
    echo Or install Chocolatey from https://chocolatey.org/install and re-run this script.
) else (
    echo Installing PortAudio via Chocolatey...
    choco install -y portaudio
)

REM Create and activate virtual environment
python -m venv venv
call venv\Scripts\activate

REM Upgrade pip and install Python dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

echo Setup complete.
echo To run the tool, use: run_win.bat
pause
