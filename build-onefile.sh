#!/bin/bash
# build-onefile.sh - Build a single-file executable using PyInstaller

set -e

echo "=========================================="
echo "Building ScreenOCR with PyInstaller"
echo "=========================================="

# Check PyInstaller is installed
if ! pip list | grep -q pyinstaller; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Get version from setup.py
VERSION=$(grep "version=" setup.py | head -1 | sed "s/.*version=['\"]\\([^'\"]*\\)['\"].*/\\1/")
echo "Building version: $VERSION"

# Create spec file
cat > screenocr.spec << 'SPEC'
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'cv2',
    'numpy',
    'rapidocr_onnxruntime',
    'PIL',
    'keyboard',
]

# Collect Qt plugins and data
datas += collect_all('PySide6')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=['matplotlib', 'scipy', 'pytest'],
    win_type_codec=None,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='screenocr',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
SPEC

# Build executable
echo "Building executable..."
pyinstaller --onefile --windowed \
    --name=screenocr \
    --icon=screenocr.png \
    --add-data="screenocr.desktop:." \
    --hidden-import=PySide6 \
    --hidden-import=cv2 \
    --hidden-import=rapidocr_onnxruntime \
    --hidden-import=PIL \
    --hidden-import=keyboard \
    main.py

echo ""
echo "=========================================="
echo "✓ Build complete!"
echo "=========================================="
echo ""
echo "Executable: dist/screenocr"
echo "Size: $(du -sh dist/screenocr | cut -f1)"
echo ""
echo "Test it:"
echo "  ./dist/screenocr --help"
echo "  ./dist/screenocr daemon start"
echo ""
