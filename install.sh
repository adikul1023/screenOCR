#!/bin/bash
# install.sh - Quick installation script for ScreenOCR

set -e

echo "=========================================="
echo "ScreenOCR Installation Script"
echo "=========================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION found"

if ! command -v spectacle &> /dev/null && \
   ! command -v gnome-screenshot &> /dev/null && \
   ! command -v flameshot &> /dev/null && \
   ! command -v scrot &> /dev/null; then
    echo "⚠ Warning: No screenshot tool found (spectacle, gnome-screenshot, flameshot, scrot)"
    echo "   Install one with: sudo apt install spectacle"
    echo ""
fi

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

echo "Activating venv..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -q -e .
echo "✓ Dependencies installed"

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the daemon:"
echo "   python main.py daemon start"
echo ""
echo "   Or with sudo (if not using udev rules):"
echo "   sudo python main.py daemon start"
echo ""
echo "2. Once running, press Super+Shift+T to trigger OCR"
echo ""
echo "3. View daemon status:"
echo "   python main.py daemon status"
echo ""
echo "4. Stop the daemon:"
echo "   python main.py daemon stop"
echo ""
echo "For more info, see README.md"
echo ""
