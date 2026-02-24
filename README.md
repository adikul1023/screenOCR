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

## Quick Install

### Option 1: AppImage (Easiest - Works Everywhere)

```bash
# Download the latest AppImage
wget https://github.com/adikul1023/screenOCR/releases/download/latest/ScreenOCR-0.2.0-x86_64.AppImage

# Make executable
chmod +x ScreenOCR-0.2.0-x86_64.AppImage

# Start the daemon
./ScreenOCR-0.2.0-x86_64.AppImage daemon start

# Or with custom hotkey
./ScreenOCR-0.2.0-x86_64.AppImage daemon start 'alt+shift+o'
```

### Option 2: Snap (Ubuntu & Fedora)

```bash
snap install screenocr
screenocr daemon start
```

### Option 3: Flatpak (All Linux Distros)

```bash
flatpak install flathub com.github.adikul1023.screenocr
flatpak run com.github.adikul1023.screenocr daemon start
```

## Requirements

- Linux with Wayland support
- One of: `spectacle`, `gnome-screenshot`, `flameshot`, `scrot`
- `wl-copy` (for clipboard, optional - falls back to Qt)
- Root access or udev rules (for global hotkey daemon)

## Installation (From Source)

## Installation (From Source)

### 1. Clone Repository

```bash
git clone https://github.com/adikul1023/screenOCR.git
cd screenOCR
```

### 2. Install Dependencies (Optional)

```bash
# Debian/Ubuntu
sudo apt install spectacle wl-clipboard python3-venv

# Fedora
sudo dnf install spectacle wl-clipboard python3-venv

# Arch
sudo pacman -S spectacle wl-clipboard
```

### 3. Install Python Package

```bash
pip install -e .
```

That's it! Now run:

```bash
screenocr daemon start
```

## Usage

### Start Daemon (Global Hotkey)

```bash
screenocr daemon start
```

Then press **Super+Shift+T** to trigger OCR.

### Custom Hotkey

```bash
screenocr daemon start 'ctrl+shift+c'
screenocr daemon start 'alt+shift+o'
screenocr daemon start 'super+alt+x'
```

### Manual Trigger (No Daemon)

```bash
screenocr trigger
```

### Control Daemon

```bash
screenocr daemon status    # Check if running
screenocr daemon stop      # Stop daemon
```

### Auto-Start on Login (Optional)

Using systemd:

```bash
mkdir -p ~/.config/systemd/user
cp screenocr-daemon.service ~/.config/systemd/user/
systemctl --user enable screenocr-daemon
systemctl --user start screenocr-daemon
```

View logs:

```bash
journalctl --user -u screenocr-daemon -f
```

## Troubleshooting

### Hotkey not working?

**Error:** `Permission denied` or module errors

**Solution:** Run with sudo
```bash
sudo screenocr daemon start
```

Or configure udev rules (see PACKAGING.md)

### Screenshot tool not found?

**Error:** `spectacle not found`

**Solution:** Install a screenshot tool
```bash
sudo apt install spectacle  # or gnome-screenshot, flameshot
```

### Clipboard not working?

**Error:** Text not copying

**Solution:** Install wl-copy (optional, falls back to Qt)
```bash
sudo apt install wl-clipboard
```

## Performance

- **Startup:** ~1-2 seconds
- **OCR:** ~0.5-1 second
- **Total latency:** ~2-3 seconds from hotkey press

## Distribution Formats

See [PACKAGING.md](PACKAGING.md) for details on:
- **AppImage** - Single file, works everywhere
- **Snap** - Ubuntu/Fedora snapcraft
- **Flatpak** - Modern Linux standard
- **Traditional packages** - .deb, .rpm, AUR

## Architecture

```
hotkey_daemon.py   → Global hotkey listener
        ↓
main.py            → Launches GUI on hotkey
        ↓
overlay.py         → Region selection overlay
        ↓
portal.py          → XDG Portal screenshot (Wayland-safe)
        ↓
ocr_engine.py      → RapidOCR processing
        ↓
Clipboard          → Auto-copy result
```

## Development

```bash
# Run tests
python test_ocr.py

# Manual trigger
python main.py trigger

# Check daemon
python main.py daemon status
```

## Building Packages

See [PACKAGING.md](PACKAGING.md) for:
- Building AppImage
- Building Snap
- Building Flatpak
- GitHub Actions CI/CD setup

Quick build:
```bash
bash build-appimage.sh
```

## License

MIT - See LICENSE file

## Credits

- **RapidOCR** - OCR engine
- **PySide6** - Qt bindings
- **keyboard** - Hotkey support
- **XDG Portal** - Wayland screenshot

## Links

- **GitHub:** https://github.com/adikul1023/screenOCR
- **Issues:** https://github.com/adikul1023/screenOCR/issues
- **Releases:** https://github.com/adikul1023/screenOCR/releases
