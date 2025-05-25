#!/bin/bash

echo "Installing dependencies for macOS..."

# Ensure Homebrew is installed
if ! command -v brew &>/dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Python and PortAudio
brew install python portaudio

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete. To start the tool:"
echo "source venv/bin/activate && python main.py"