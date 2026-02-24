"""
Setup script for ScreenOCR - Global hotkey-triggered OCR utility for Linux/Wayland.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read requirements
requirements = [
    line.strip() 
    for line in Path('requirements.txt').read_text().splitlines()
    if line.strip() and not line.startswith('#')
]

# Read long description
long_description = """
# ScreenOCR - Wayland OCR Utility

A fast, lightweight OCR tool for Linux with global hotkey support.
Triggered with Super+Shift+T (customizable) to extract text or code from any screen region.

Features:
- Fast RapidOCR engine (~1-2 second response time)
- Wayland-native screenshot support via XDG Portal
- Global hotkey daemon (requires keyboard library privileges)
- Smart Python syntax post-processing
- Clipboard integration (wl-copy/Qt fallback)
- Advanced image preprocessing (denoising, contrast enhancement, upscaling)

Requirements:
- Linux with Wayland support
- spectacle, gnome-screenshot, or similar screenshot tool
- wl-copy for clipboard (optional, falls back to Qt)

Installation:
    pip install -e .
    screenocr daemon start

Usage:
    # Start the hotkey daemon
    screenocr daemon start
    
    # Stop the daemon
    screenocr daemon stop
    
    # Check daemon status
    screenocr daemon status
    
    # Manual trigger (testing)
    screenocr trigger
"""

setup(
    name='screenocr',
    version='0.2.0',
    description='Fast hotkey-triggered OCR for Linux/Wayland',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='OCR Developer',
    author_email='dev@screenocr.local',
    url='https://github.com/adikul1023/screenOCR',
    license='MIT',
    
    # Package configuration
    py_modules=['main', 'ocr_engine', 'portal', 'overlay', 'utils', 'hotkey_daemon'],
    packages=find_packages(),
    
    # Dependencies
    install_requires=requirements,
    
    # Entry points for CLI commands
    entry_points={
        'console_scripts': [
            'screenocr=main:cli_main',
        ],
    },
    
    # Metadata
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Office/Business',
        'Topic :: Multimedia :: Graphics :: Capture',
    ],
    
    python_requires='>=3.10',
    
    # Project URLs
    project_urls={
        'Source': 'https://github.com/adikul1023/screenOCR',
        'Issues': 'https://github.com/adikul1023/screenOCR/issues',
    },
)
