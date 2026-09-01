#!/bin/bash

# ScreenOCR 1-Click Installer
# Run via: curl -sSL https://raw.githubusercontent.com/adikul1023/screenOCR/main/install.sh | bash

set -e

echo -e "\n============================================="
echo -e "      ScreenOCR - 1-Click Installer          "
echo -e "=============================================\n"

APP_DIR="$HOME/.local/share/screenocr"
VENV_DIR="$APP_DIR/venv"
SRC_DIR="$APP_DIR/src"
BIN_DIR="$HOME/.local/bin"

echo "[1/5] Setting up directories..."
mkdir -p "$APP_DIR"
mkdir -p "$BIN_DIR"

echo "[2/5] Setting up source code..."
if [ -f "$PWD/main.py" ]; then
    echo "Local installation detected. Copying files..."
    rm -rf "$SRC_DIR"
    mkdir -p "$SRC_DIR"
    cp -r "$PWD/"* "$SRC_DIR/"
else
    echo "Downloading latest source code from GitHub..."
    if [ -d "$SRC_DIR" ]; then
        cd "$SRC_DIR"
        git pull origin main --quiet
    else
        git clone https://github.com/adikul1023/screenOCR.git "$SRC_DIR" --quiet
    fi
fi

echo "[3/5] Setting up local Python environment (bypassing system pip limits)..."
# Find python3
PYTHON=""
for py in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$py" &> /dev/null; then
        PYTHON="$py"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Error: Python 3 is not installed on this system."
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON" -m venv "$VENV_DIR"
fi

echo "Installing Python dependencies (this may take a minute)..."
"$VENV_DIR/bin/pip" install -q PySide6 opencv-python rapidocr-onnxruntime pillow numpy keyboard

echo "[4/5] Configuring system commands..."
cat << EOF > "$BIN_DIR/screenocr"
#!/bin/bash
export PYTHONPATH="$SRC_DIR:\$PYTHONPATH"
exec "$VENV_DIR/bin/python3" "$SRC_DIR/main.py" "\$@"
EOF
chmod +x "$BIN_DIR/screenocr"

# Ensure ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "\nNote: ~/.local/bin is not in your PATH."
    echo "Please add 'export PATH=\"\$HOME/.local/bin:\$PATH\"' to your ~/.bashrc or ~/.config/fish/config.fish"
fi

echo -e "\n[5/5] Configuring background daemon..."
echo -e "What hotkey would you like to use to trigger ScreenOCR?"
echo -e "Examples: 'super+shift+t', 'ctrl+alt+o', 'f8'"
read -p "Enter hotkey [default: super+shift+t]: " USER_HOTKEY
HOTKEY=${USER_HOTKEY:-super+shift+t}

# Setup systemd user service for auto-start
mkdir -p ~/.config/systemd/user
cat << EOF > ~/.config/systemd/user/screenocr.service
[Unit]
Description=ScreenOCR Background Hotkey Daemon
After=graphical-session.target

[Service]
Type=simple
ExecStart=$BIN_DIR/screenocr daemon start '$HOTKEY'
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable screenocr.service --now >/dev/null 2>&1 || true

# Stop any running old daemon and start new
"$BIN_DIR/screenocr" daemon stop >/dev/null 2>&1 || true
"$BIN_DIR/screenocr" daemon start "$HOTKEY" >/dev/null 2>&1 &

echo -e "\n============================================="
echo -e "              INSTALLATION COMPLETE            "
echo -e "=============================================\n"
echo -e "✓ The command 'screenocr' is now available globally!"
echo -e "✓ The background daemon is running and will start on login."
echo -e "\nTry it now by pressing:  $HOTKEY"
echo -e "\nOr trigger it manually:  screenocr trigger"
echo -e "=============================================\n"
