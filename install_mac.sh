#!/bin/bash

echo "Installing dependencies for macOS..."

# Ensure Homebrew is installed
if ! command -v brew &>/dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Python
brew install python

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Test sounddevice
python -c "import sounddevice; print('[INFO] sounddevice loaded:', sounddevice.query_devices())" || echo '[WARNING] sounddevice may not be working correctly.'

echo "Setup complete."
echo "To run the tool, use: ./run_mac.sh"
