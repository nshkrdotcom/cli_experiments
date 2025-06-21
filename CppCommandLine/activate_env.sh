#!/bin/bash
# Simple activation script for the virtual environment

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "Virtual environment created."
fi

echo "Activating virtual environment..."
source venv/bin/activate

if [ ! -f "venv/pyvenv.cfg" ] || ! pip show repl-nix-workspace > /dev/null 2>&1; then
    echo "Installing dependencies..."
    pip install -e .
    echo "Dependencies installed."
fi

echo "Virtual environment activated and ready!"
echo "You can now run: python main.py --help"
echo "To deactivate, run: deactivate" 