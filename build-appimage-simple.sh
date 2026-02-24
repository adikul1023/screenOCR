#!/bin/bash
# build-appimage-simple.sh - Simplified AppImage builder

set -e

APP_VERSION="0.2.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
APPDIR="${BUILD_DIR}/ScreenOCR.AppDir"

echo "=========================================="
echo "Building ScreenOCR AppImage (Simplified)"
echo "=========================================="

# Check appimagetool (local or system)
APPIMAGETOOL=""
if [ -x "${SCRIPT_DIR}/appimagetool" ]; then
    APPIMAGETOOL="${SCRIPT_DIR}/appimagetool"
    echo "Using local appimagetool"
elif command -v appimagetool &> /dev/null; then
    APPIMAGETOOL="appimagetool"
    echo "Using system appimagetool"
else
    echo "✗ appimagetool not found!"
    echo "Downloading appimagetool..."
    wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage -O "${SCRIPT_DIR}/appimagetool"
    chmod +x "${SCRIPT_DIR}/appimagetool"
    APPIMAGETOOL="${SCRIPT_DIR}/appimagetool"
fi

echo "[1/4] Creating AppDir structure..."
rm -rf "${BUILD_DIR}"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

echo "[2/4] Copying application files..."
# Copy Python modules
cp "${SCRIPT_DIR}/main.py" "${APPDIR}/"
cp "${SCRIPT_DIR}/ocr_engine.py" "${APPDIR}/"
cp "${SCRIPT_DIR}/portal.py" "${APPDIR}/"
cp "${SCRIPT_DIR}/overlay.py" "${APPDIR}/"
cp "${SCRIPT_DIR}/utils.py" "${APPDIR}/"
cp "${SCRIPT_DIR}/hotkey_daemon.py" "${APPDIR}/"

# Copy desktop file
cp "${SCRIPT_DIR}/screenocr.desktop" "${APPDIR}/usr/share/applications/"
cp "${SCRIPT_DIR}/screenocr.desktop" "${APPDIR}/"

# Create simple icon (text-based for now)
echo "Creating placeholder icon..."
cat > "${APPDIR}/screenocr.png" << 'ICON'
iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==
ICON
base64 -d "${APPDIR}/screenocr.png" > "${APPDIR}/usr/share/icons/hicolor/256x256/apps/screenocr.png" 2>/dev/null || true
cp "${APPDIR}/screenocr.png" "${APPDIR}/.DirIcon" 2>/dev/null || true

echo "[3/4] Creating AppRun wrapper..."
# Note: AppImage will use system Python and packages
# User must have dependencies installed via pip/apt
cat > "${APPDIR}/AppRun" << 'APPRUN'
#!/bin/bash
# AppRun for ScreenOCR

APPDIR="$(dirname "$(readlink -f "${0}")")"

# Find Python 3
PYTHON=""
for py in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$py" &> /dev/null; then
        PYTHON="$py"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Error: Python 3 not found!"
    exit 1
fi

# Check dependencies
if ! $PYTHON -c "import PySide6" 2>/dev/null; then
    echo "Error: PySide6 not installed!"
    echo "Install with: pip install PySide6 opencv-python rapidocr-onnxruntime pillow numpy keyboard"
    exit 1
fi

# Add AppDir to Python path
export PYTHONPATH="${APPDIR}:${PYTHONPATH}"

# Run the application
cd "${APPDIR}"
exec $PYTHON "${APPDIR}/main.py" "$@"
APPRUN

chmod +x "${APPDIR}/AppRun"

echo "[4/4] Building AppImage..."

# Use ARCH environment variable for appimagetool
export ARCH=x86_64

# Build AppImage
"${APPIMAGETOOL}" --no-appstream "${APPDIR}" "${SCRIPT_DIR}/ScreenOCR-${APP_VERSION}-x86_64.AppImage"

# Make executable
chmod +x "${SCRIPT_DIR}/ScreenOCR-${APP_VERSION}-x86_64.AppImage"

echo ""
echo "=========================================="
echo "✓ AppImage created successfully!"
echo "=========================================="
echo ""
ls -lh "${SCRIPT_DIR}/ScreenOCR-${APP_VERSION}-x86_64.AppImage"
echo ""
echo "Size: $(du -sh "${SCRIPT_DIR}/ScreenOCR-${APP_VERSION}-x86_64.AppImage" | cut -f1)"
echo ""
echo "Note: Users need Python 3 and dependencies installed:"
echo "  pip install PySide6 opencv-python rapidocr-onnxruntime pillow numpy keyboard"
echo ""
echo "Usage:"
echo "  ./ScreenOCR-${APP_VERSION}-x86_64.AppImage daemon start"
echo "  ./ScreenOCR-${APP_VERSION}-x86_64.AppImage trigger"
echo ""
