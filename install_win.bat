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
    echo PortAudio cannot be installed automatically via Chocolatey.
    echo Please download the PortAudio DLL manually from:
    echo   https://www.portaudio.com/download.html
    echo and place portaudio_x64.dll (or portaudio.dll) in the project folder, venv\Scripts, or a folder in your PATH.
)

REM Create and activate virtual environment
python -m venv venv
call venv\Scripts\activate

REM Upgrade pip and install Python dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo IMPORTANT: If you see audio playback issues, ensure you have manually downloaded the PortAudio DLL and placed it in the correct location as described above.
echo Setup complete.
echo To run the tool, use: run_win.bat
pause
