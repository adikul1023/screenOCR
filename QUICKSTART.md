# 🚀 ScreenOCR - Quick Start

## The Easiest Way: AppImage (Just Works!)

```bash
# 1. Download
wget https://github.com/adikul1023/screenOCR/releases/download/v0.2.0/ScreenOCR.AppImage

# 2. Make executable
chmod +x ScreenOCR.AppImage

# 3. Run!
./ScreenOCR.AppImage trigger
```

**That's it!** No manual setup needed. The AppImage automatically:
- ✅ Checks for Python packages
- ✅ Installs missing dependencies
- ✅ Checks system requirements
- ✅ Handles everything automatically

---

## Set Up Global Hotkey (Optional)

Get OCR with a single keystroke anywhere on your desktop:

### KDE Plasma (Recommended)

1. Open **System Settings** → **Shortcuts** → **Custom Shortcuts**
2. Click **Edit** → **New** → **Global Shortcut** → **Command/URL**
3. **Trigger tab:** Set to `Super+Shift+T` (or your preference)
4. **Action tab:** Enter:
   ```
   /path/to/ScreenOCR.AppImage trigger
   ```
5. Click **Apply**

### GNOME

1. Open **Settings** → **Keyboard** → **Custom Shortcuts**
2. Create a new shortcut:
   - **Name:** ScreenOCR
   - **Command:** `/path/to/ScreenOCR.AppImage trigger`
3. Press desired key combination

See [HOTKEY-SETUP.md](HOTKEY-SETUP.md) for XFCE, i3, Sway, and others.

---

## Usage

### Method 1: Hotkey (After Setup)
Press **Super+Shift+T** anywhere, then:
1. Drag to select region
2. Release to extract text
3. ✓ Text auto-copied to clipboard

### Method 2: Manual Trigger
```bash
./ScreenOCR.AppImage trigger
```

Same process as hotkey.

---

## Alternative Distributions

### Flatpak (When Available)

```bash
# Install
flatpak install screenocr.flatpak

# Run  
flatpak run com.github.adikul1023.screenocr trigger
```

Flatpak handles all dependencies automatically too!

### From Source (Developers)

```bash
git clone https://github.com/adikul1023/screenOCR.git
cd screenOCR
pip install -r requirements.txt
python main.py trigger
```

---

## Troubleshooting

### "Python 3 not found"

Get Python 3:
```bash
# Ubuntu/Debian
sudo apt install python3

# Fedora
sudo dnf install python3

# Arch
sudo pacman -S python
```

### Dependencies not installing?

The AppImage tries to auto-install. If it fails, install manually:
```bash
pip install PySide6 opencv-python rapidocr-onnxruntime pillow numpy keyboard
```

### Still not working?

Open an [issue](https://github.com/adikul1023/screenOCR/issues) with:
```bash
./ScreenOCR.AppImage trigger --help
```

---

## What It Does

1. Press hotkey / run AppImage
2. Select region on screen
3. OCR text extracted instantly
4. Text in clipboard, ready to paste!

**Perfect for:**
- 📝 Code snippets
- 📖 Documentation
- 🖼️ Screenshots
- 📺 Terminal output
- 🎬 Presentations

---

## Questions?

- 📚 [README.md](README.md) - Full documentation
- ⌨️ [HOTKEY-SETUP.md](HOTKEY-SETUP.md) - Hotkey configuration
- 📦 [PACKAGING.md](PACKAGING.md) - Build & distribution
- 🐛 [Issues](https://github.com/adikul1023/screenOCR/issues)
