# ScreenOCR Distribution & Packaging Guide

Choose your preferred distribution method:

## 🚀 Quick Start (AppImage)

**The easiest way for users to install:**

```bash
# Download the AppImage
wget https://github.com/adikul1023/screenOCR/releases/download/v0.2.0/ScreenOCR-0.2.0-x86_64.AppImage

# Make it executable
chmod +x ScreenOCR-0.2.0-x86_64.AppImage

# Run it
./ScreenOCR-0.2.0-x86_64.AppImage daemon start
```

### Build AppImage

```bash
bash build-appimage.sh
```

**Requirements:**
- `appimagetool` (recommended): `wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage`
- Or `linuxdeploy` + `linuxdeploy-plugin-appimage`
- Or fallback to tar.gz

The AppImage is:
- ✅ Single file, no installation needed
- ✅ Works on any modern Linux distro
- ✅ Easy to distribute
- ✅ Can be made portable

---



```bash

# Or build locally
```

**Advantages:**
- Auto-updates
- Sandboxed environment
- Simple installation

**Installation:**
```bash
screenocr daemon start
```

---


**Modern, portable package format:**

```bash
# Build locally

```

**Installation:**
```bash
```

**Advantages:**
- Works on all Linux distros
- Sandboxed for security
- Easy versioning

---

## 🐧 Traditional Packages (.deb, .rpm)

For Debian/Ubuntu users:
```bash
# Create .deb
fpm -s python -t deb -n screenocr -v 0.2.0 setup.py

# Install
dpkg -i screenocr_0.2.0_amd64.deb
screenocr daemon start
```

For Fedora/RHEL users:
```bash
# Create .rpm
fpm -s python -t rpm -n screenocr -v 0.2.0 setup.py

# Install
sudo rpm -i screenocr-0.2.0-1.x86_64.rpm
screenocr daemon start
```

---

## 📋 Distribution Matrix

| Format | Distros | Setup | Auto-Update | Notes |
|--------|---------|-------|-------------|-------|
| **AppImage** | All | Single file | ❌ (Manual) | **Most portable** |
| **.deb** | Debian/Ubuntu | `apt-get install` | ✅ (via repo) | Traditional |
| **.rpm** | Fedora/RHEL | `dnf/yum install` | ✅ (via repo) | Traditional |
| **AUR** | Arch/Manjaro | `yay -S screenocr` | ✅ | Arch community |

---

## 🔧 Build Requirements

### For AppImage:
```bash
# Debian/Ubuntu
apt-get install python3-dev libssl-dev libffi-dev

# Fedora
dnf install python3-devel openssl-devel libffi-devel

# Optional: appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
```

```bash
# or
```

```bash
```

### For traditional packages:
```bash
gem install fpm
# or
pip install fpm
```

---

## 📝 Release Process

### 1. **Version Bump**
```bash
# Update version in:
# - setup.py
# - pyproject.toml
# - com.github.adikul1023.screenocr.yml

# Commit
git add .
git commit -m "Bump version to 0.2.1"
git tag -a v0.2.1 -m "Release v0.2.1"
git push origin master --tags
```

### 2. **Build Distributions**
```bash
# Build AppImage
bash build-appimage.sh
# → ScreenOCR-0.2.1-x86_64.AppImage


```

### 3. **Create GitHub Release**
```bash
# Draft release on GitHub
# Upload:
# - ScreenOCR-0.2.1-x86_64.AppImage
```

### 4. **Upload to Stores**
```bash


# AUR (if maintaining)
cd screenocr-aur
git add .
git commit -m "Update to 0.2.1"
git push aur master
```

---

## 🎯 Recommended Distribution Strategy

**For maximum reach:**

1. **Primary:** AppImage (works everywhere)
4. **Community:** AUR (Arch users)

**Upload to:**
- GitHub Releases (all formats)
- AUR (if community maintains)

---

## 📚 Example: Building and Releasing

```bash
#!/bin/bash
# build-release.sh - Complete release build

VERSION="0.2.1"

echo "Building AppImage..."
bash build-appimage.sh
mv ScreenOCR-*.AppImage "ScreenOCR-${VERSION}-x86_64.AppImage"



echo "✓ Build complete!"

echo ""
echo "Next: Upload to GitHub Releases"
```

---

## ❓ FAQ

**Q: Which format should I use?**  

**Q: Can I automatically update AppImages?**  
A: Use `AppImageUpdate` libraries or recommend users use a package manager instead.


**Q: What about Windows/macOS?**  
A: Not supported currently (Wayland-specific). Could use pyinstaller for Windows version.

**Q: How big is the AppImage?**  
A: ~200-300MB depending on bundled dependencies.

---

## 🔗 Useful Links

- **AppImage:** https://appimage.org/
- **GitHub Releases:** https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
- **AUR:** https://wiki.archlinux.org/title/AUR

