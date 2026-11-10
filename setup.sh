#!/usr/bin/env bash
echo "installing pyenv"
curl -fsSL https://pyenv.run | bash

echo "installing python version using pyenv"
pyenv install 3.11.7

set -e

cd ~/Documents/JARVIS_BMOS

echo "Creating virtual environment..."
python3 -m venv .venv

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing FFmpeg..."

# Ubuntu/Debian
if command -v apt >/dev/null 2>&1; then
    sudo apt update
    sudo apt install -y ffmpeg portaudio19-dev python3-dev

# macOS
elif command -v brew >/dev/null 2>&1; then
    brew install ffmpeg portaudio

else
    echo "Unsupported package manager."
    echo "Please install FFmpeg and PortAudio manually."
fi

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('cmudict')"

echo ""
echo "Setup complete."
echo ""
echo "Activate environment with:"
echo "source .venv/bin/activate"