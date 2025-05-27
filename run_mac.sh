#!/bin/bash

echo "==============================="
echo " Starting Chord Progression Tool"
echo "==============================="

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
  echo "[ERROR] Virtual environment not found."
  echo "Please run install_mac.sh first to set up the environment."
  exit 1
fi

# Activate and run
source venv/bin/activate
python main.py
