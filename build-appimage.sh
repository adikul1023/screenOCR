#!/bin/bash
# build-appimage.sh - Build ScreenOCR as AppImage

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
APPDIR="${BUILD_DIR}/ScreenOCR.AppDir"
APP_VERSION="0.2.0"
PYTHON_VERSION="3.13"

echo "=========================================="
echo "Building ScreenOCR AppImage"
echo "=========================================="

# Check dependencies
echo "[1/5] Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "✗ pip not found"
    exit 1
fi

# Create AppDir structure
echo "[2/5] Creating AppImage directory structure..."
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/lib"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons"

# Copy application files
echo "[3/5] Copying application files..."
cp "${SCRIPT_DIR}/main.py" "${APPDIR}/"
cp "${SCRIPT_DIR}/ocr_engine.py" "${APPDIR}/"
cp "${SCRIPT_DIR}/portal.py" "${APPDIR}/"
cp "${SCRIPT_DIR}/overlay.py" "${APPDIR}/"
cp "${SCRIPT_DIR}/utils.py" "${APPDIR}/"
cp "${SCRIPT_DIR}/hotkey_daemon.py" "${APPDIR}/"
cp "${SCRIPT_DIR}/screenocr.desktop" "${APPDIR}/usr/share/applications/"
cp "${SCRIPT_DIR}/AppRun" "${APPDIR}/"
chmod +x "${APPDIR}/AppRun"

# Create a simple launcher script
cat > "${APPDIR}/screenocr" << 'LAUNCHER'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from main import cli_main
if __name__ == '__main__':
    sys.exit(cli_main())
LAUNCHER
chmod +x "${APPDIR}/screenocr"

# Bundle Python dependencies
echo "[4/5] Creating Python environment..."

# Create a minimal venv inside AppDir
python3 -m venv "${APPDIR}/venv" --system-site-packages

# Copy venv to AppDir
cp -r "${SCRIPT_DIR}/venv-sys/lib/python${PYTHON_VERSION}/site-packages"/* \
    "${APPDIR}/venv/lib/python${PYTHON_VERSION}/site-packages/" 2>/dev/null || true

# Create a wrapper for the venv
mkdir -p "${APPDIR}/usr/bin"
cat > "${APPDIR}/usr/bin/python3" << 'PYWRAPPER'
#!/bin/bash
APPDIR="$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")"
export PYTHONHOME="${APPDIR}/venv"
exec "${APPDIR}/venv/bin/python3" "$@"
PYWRAPPER
chmod +x "${APPDIR}/usr/bin/python3"

# Copy runtime libraries
echo "[5/5] Finalizing AppImage..."

if command -v appimagetool &> /dev/null; then
    # Use appimagetool if available
    echo "Creating AppImage using appimagetool..."
    appimagetool "${APPDIR}" "${SCRIPT_DIR}/ScreenOCR-${APP_VERSION}-x86_64.AppImage"
    chmod +x "${SCRIPT_DIR}/ScreenOCR-${APP_VERSION}-x86_64.AppImage"
    echo ""
    echo "✓ AppImage created: ScreenOCR-${APP_VERSION}-x86_64.AppImage"
    echo ""
    echo "Usage:"
    echo "  ./ScreenOCR-${APP_VERSION}-x86_64.AppImage daemon start"
    echo "  ./ScreenOCR-${APP_VERSION}-x86_64.AppImage trigger"
    
elif command -v linuxdeploy &> /dev/null; then
    # Use linuxdeploy if available
    echo "Creating AppImage using linuxdeploy..."
    
    # Create desktop file
    linuxdeploy --appimage-format AppImage \
        --desktop-file="${APPDIR}/usr/share/applications/screenocr.desktop" \
        --directory="${APPDIR}" \
        --output appimage \
        --custom-apprun="${APPDIR}/AppRun"
    
else
    # Fallback: create tarball instead
    echo "⚠ appimagetool and linuxdeploy not found"
    echo "Creating tar.gz instead..."
    
    cd "${BUILD_DIR}"
    tar czf "${SCRIPT_DIR}/ScreenOCR-${APP_VERSION}-x86_64.tar.gz" ScreenOCR.AppDir/
    echo ""
    echo "✓ Tarball created: ScreenOCR-${APP_VERSION}-x86_64.tar.gz"
    echo ""
    echo "To use:"
    echo "  tar xzf ScreenOCR-${APP_VERSION}-x86_64.tar.gz"
    echo "  cd ScreenOCR.AppDir"
    echo "  ./AppRun daemon start"
fi

echo ""
echo "=========================================="
echo "✓ Build complete!"
echo "=========================================="
echo ""
echo "Distribution files:"
ls -lh "${SCRIPT_DIR}"/ScreenOCR* 2>/dev/null || echo "  (See build directory)"
echo ""
