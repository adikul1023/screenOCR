# ScreenOCR - Global Hotkey-Triggered OCR for Linux/Wayland

A fast, lightweight OCR utility for Linux with global hotkey support. Press **Super+Shift+T** to extract text or code from any screen region.

## Features

- ⚡ **Fast** - RapidOCR engine with ~1-2 second response time
- 🌊 **Wayland-Native** - XDG Desktop Portal screenshot support
- 🔥 **Hotkey Triggered** - Press Super+Shift+T to capture and extract
- 📋 **Smart Clipboard** - Automatically copies extracted text (wl-copy/Qt)
- 🐍 **Python Syntax Aware** - Post-processes code with smart formatting
- 🎨 **Image Preprocessing** - Denoising, contrast enhancement, upscaling
- ⚙️ **Configurable** - Customize hotkey and behavior

## Requirements

- Linux with Wayland support
- Python 3.10+
- One of: `spectacle`, `gnome-screenshot`, `flameshot`, `scrot`
- `wl-copy` (for clipboard, optional - falls back to Qt)
- Root access or configured udev rules (for global hotkey)

## Installation

### 1. Clone and Setup

```bash
cd ~/Documents/OCR  # or your preferred location
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Install System Dependencies

**Fedora/RHEL:**
```bash
sudo dnf install spectacle wl-clipboard
```

**Ubuntu/Debian:**
```bash
sudo apt install spectacle wl-clipboard
```

**Arch:**
```bash
sudo pacman -S spectacle wl-clipboard
```

### 3. Setup Hotkey Daemon

The keyboard library requires elevated privileges. Choose one:

#### Option A: Run with sudo (Easiest)
```bash
sudo ~/.local/bin/screenocr daemon start
# Or with modified hotkey:
sudo ~/.local/bin/screenocr daemon start 'ctrl+shift+c'
```

#### Option B: Configure udev Rules (Advanced, one-time)
```bash
sudo groupadd uinput
sudo usermod -a -G uinput $USER
sudo echo 'SUBSYSTEM=="uinput", GROUP="uinput", MODE="0660"' | sudo tee /etc/udev/rules.d/99-uinput.rules
sudo udevadm control --reload
# Log out and log back in
```

Then run without sudo:
```bash
~/.local/bin/screenocr daemon start
```

#### Option C: Autostart via systemd (Linux)

Copy systemd service:
```bash
mkdir -p ~/.config/systemd/user
cp screenocr-daemon.service ~/.config/systemd/user/

# Edit to use sudo if needed
systemctl --user enable screenocr-daemon
systemctl --user start screenocr-daemon
```

## Usage

### Start the Daemon
```bash
# With sudo
sudo screenocr daemon start

# Or with custom hotkey
sudo screenocr daemon start 'alt+shift+o'
```

### Stop the Daemon
```bash
screenocr daemon stop
```

### Check Status
```bash
screenocr daemon status
```

### Manual Trigger (Testing)
```bash
screenocr trigger
```

### View Logs (systemd)
```bash
journalctl --user -u screenocr-daemon -f
```

## Supported Hotkeys

Common hotkey combinations:
- `super+shift+t` - Windows/Super key + Shift + T (default)
- `ctrl+shift+c` - Control + Shift + C
- `alt+shift+o` - Alt + Shift + O
- `ctrl+alt+o` - Control + Alt + O

Format: Use `+` to separate keys, lowercase letters, and key names like `super`, `ctrl`, `alt`, `shift`.

## Configuration

Configuration is saved in `~/.config/screenocr/config.json`:
```json
{
  "hotkey": "super+shift+t",
  "version": "1.0",
  "launched": 1234567890
}
```

## Troubleshooting

### Hotkey not working
1. Check daemon is running: `screenocr daemon status`
2. Check permissions: Daemon needs keyboard input access
3. Some display managers may intercept hotkeys - try a different combination

### Screenshot not working
- Ensure one of: `spectacle`, `gnome-screenshot`, `flameshot`, `scrot` is installed
- On Wayland: `spectacle` is preferred

### Clipboard not working
- `wl-copy` not installed: `sudo apt install wl-clipboard`
- Falls back to Qt clipboard automatically

### Module not found errors
- Reinstall: `pip install -e --force-reinstall .`
- Check Python path: `which python` should match venv

## Performance

- Startup time: ~1-2 seconds (RapidOCR)
- OCR processing: ~0.5-1 second
- Total latency: ~2-3 seconds from hotkey press to clipboard ready

## Architecture

```
hotkey_daemon.py    ← Listens for global hotkeys (runs as daemon)
    ↓
main.py             ← Launches GUI when triggered
    ↓
overlay.py          ← Shows selection rectangle overlay
    ↓
portal.py           ← Captures screenshot via XDG Portal (Wayland-safe)
    ↓
ocr_engine.py       ← Processes image with RapidOCR
    ↓
clipboard           ← Copies result (wl-copy or Qt)
```

## Development

### Run tests
```bash
python test_ocr.py
```

### Manual trigger
```bash
python main.py trigger
```

### Check imports
```bash
python -c "from ocr_engine import OCREngine; print('✓ OCR working')"
```

## License

MIT - See LICENSE file

## Credits

- RapidOCR - Fast OCR engine
- PySide6 - Qt bindings for Python
- keyboard - Global hotkey library
- XDG Desktop Portal - Wayland screenshot support

## Links

- GitHub: https://github.com/adikul1023/screenOCR
- Issues: https://github.com/adikul1023/screenOCR/issues
