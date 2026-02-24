# 🚀 ScreenOCR - Quick Start

## The Fastest Way to Get Started

### For Most Users: Download AppImage (Recommended ✅)

```bash
# 1. Download (choose one)
wget https://github.com/adikul1023/screenOCR/releases/download/v0.2.0/ScreenOCR-0.2.0-x86_64.AppImage

# 2. Make executable
chmod +x ScreenOCR-0.2.0-x86_64.AppImage

# 3. Run it!
./ScreenOCR-0.2.0-x86_64.AppImage daemon start
```

**Done!** Press `Super+Shift+T` (Windows key + Shift + T) to extract text from any screen region.

---

## Alternative Installation Methods

### Ubuntu/Fedora: Snap (Auto-Updates ✨)

```bash
snap install screenocr
screenocr daemon start
```

### Any Linux: Flatpak (Modern 🔐)

```bash
flatpak install flathub com.github.adikul1023.screenocr
flatpak run com.github.adikul1023.screenocr daemon start
```

### From Source (Development 🛠️)

```bash
git clone https://github.com/adikul1023/screenOCR.git
cd screenOCR
pip install -e .
screenocr daemon start
```

---

## Usage

Once running, press your hotkey:

- **Super+Shift+T** (Default) - Select region, extract text
- **Text auto-copies to clipboard** ✓

Change hotkey:
```bash
./ScreenOCR-0.2.0-x86_64.AppImage daemon start 'ctrl+shift+c'
```

Stop daemon:
```bash
./ScreenOCR-0.2.0-x86_64.AppImage daemon stop
./ScreenOCR-0.2.0-x86_64.AppImage daemon status
```

---

## Need Help?

- 📖 Full docs: [README.md](README.md)
- 🐛 Issues: [GitHub Issues](https://github.com/adikul1023/screenOCR/issues)
- 📦 Packaging: [PACKAGING.md](PACKAGING.md)

---

## System Requirements

- Linux with Wayland ✓
- One of: `spectacle`, `gnome-screenshot`, `flameshot`
- `wl-copy` (optional, for clipboard)

Install missing tools:
```bash
# Debian/Ubuntu
sudo apt install spectacle wl-clipboard

# Fedora
sudo dnf install spectacle wl-clipboard

# Arch
sudo pacman -S spectacle wl-clipboard
```

---

## Features

- ⚡ Fast (1-2 second response)
- 🌊 Wayland-native
- 🔥 Global hotkey + daemon
- 📋 Smart clipboard
- 🐍 Python-aware syntax

---

## What It Does

1. Press Super+Shift+T
2. Select region with mouse
3. Text extracted and copied to clipboard
4. Paste anywhere!

Perfect for:
- Code snippets
- Documentation
- Text in images
- Terminal output
- Presentations

---

## Troubleshooting

### Hotkey not working?

**If you see permission errors, use sudo:**
```bash
sudo ./ScreenOCR-*.AppImage daemon start
```

### Screenshot tool missing?

Install spectacle or gnome-screenshot:
```bash
sudo apt install spectacle
```

### No text extracted?

Try a different region with more contrast, or check logs:
```bash
./ScreenOCR-*.AppImage daemon status
```

---

## Questions?

See [README.md](README.md) or open an [issue](https://github.com/adikul1023/screenOCR/issues).
