#!/bin/bash
# create-release.sh - Create GitHub release with AppImage

VERSION="0.2.0"
TAG="v${VERSION}"

echo "=========================================="
echo "Creating GitHub Release v${VERSION}"
echo "=========================================="

# Check if AppImage exists
if [ ! -f "ScreenOCR-${VERSION}-x86_64.AppImage" ]; then
    echo "Building AppImage..."
    bash build-appimage-simple.sh
    
    # If simple build failed, try manual build
    if [ ! -f "ScreenOCR-${VERSION}-x86_64.AppImage" ]; then
        echo "Running manual build..."
        ARCH=x86_64 ./appimagetool --no-appstream build/ScreenOCR.AppDir "ScreenOCR-${VERSION}-x86_64.AppImage"
    fi
fi

if [ ! -f "ScreenOCR-${VERSION}-x86_64.AppImage" ]; then
    echo "✗ Failed to create AppImage"
    exit 1
fi

echo "✓ AppImage ready: $(ls -lh ScreenOCR-${VERSION}-x86_64.AppImage)"

# Create git tag if not exists
if ! git tag | grep -q "^${TAG}$"; then
    echo "Creating git tag ${TAG}..."
    git tag -a "${TAG}" -m "Release version ${VERSION}"
    git push origin "${TAG}"
fi

echo ""
echo "=========================================="
echo "Release Files Ready"
echo "=========================================="
echo ""
echo "AppImage: ScreenOCR-${VERSION}-x86_64.AppImage ($(du -sh ScreenOCR-${VERSION}-x86_64.AppImage | cut -f1))"
echo ""
echo "Next steps:"
echo ""
echo "1. Go to: https://github.com/adikul1023/screenOCR/releases/new"
echo "2. Select tag: ${TAG}"
echo "3. Title: ScreenOCR v${VERSION}"
echo "4. Upload: ScreenOCR-${VERSION}-x86_64.AppImage"
echo "5. Description:"
echo ""
cat << 'RELEASE_NOTES'
## ScreenOCR v0.2.0

Fast hotkey-triggered OCR for Linux/Wayland.

### Quick Start

1. Download the AppImage
2. Make executable: `chmod +x ScreenOCR-0.2.0-x86_64.AppImage`
3. Run: `./ScreenOCR-0.2.0-x86_64.AppImage daemon start`
4. Press **Super+Shift+T** to trigger OCR!

### Requirements

- Linux with Python 3.10+
- System dependencies:
  ```bash
  pip install PySide6 opencv-python rapidocr-onnxruntime pillow numpy keyboard
  ```
- Screenshot tool: `spectacle`, `gnome-screenshot`, or `flameshot`
- Optional: `wl-copy` for clipboard (falls back to Qt)

### Features

- ⚡ Fast RapidOCR engine (~1-2 second response)
- 🌊 Wayland-native XDG Portal screenshots
- 🔥 Global hotkey daemon (Super+Shift+T)
- 📋 Smart clipboard integration
- 🐍 Python syntax awareness
- ⚙️ Customizable hotkeys

### Usage

```bash
# Start daemon with default hotkey (Super+Shift+T)
./ScreenOCR-0.2.0-x86_64.AppImage daemon start

# Use custom hotkey
./ScreenOCR-0.2.0-x86_64.AppImage daemon start 'ctrl+shift+c'

# Manual trigger (no daemon)
./ScreenOCR-0.2.0-x86_64.AppImage trigger

# Check daemon status
./ScreenOCR-0.2.0-x86_64.AppImage daemon status

# Stop daemon
./ScreenOCR-0.2.0-x86_64.AppImage daemon stop
```

### Installation

See [README.md](https://github.com/adikul1023/screenOCR#readme) for:
- AppImage usage
- Snap installation
- Flatpak installation
- From source

### Changelog

- Initial release with RapidOCR engine
- Global hotkey daemon support
- Wayland-native screenshot capture
- Smart Python syntax post-processing
- AppImage distribution

RELEASE_NOTES

echo ""
echo "Or use GitHub CLI:"
echo "  gh release create ${TAG} ScreenOCR-${VERSION}-x86_64.AppImage --title 'ScreenOCR v${VERSION}' --notes-file CHANGELOG.md"
echo ""
