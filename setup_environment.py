"""
Environment setup and dependency checker for ScreenOCR.
Automatically installs missing dependencies without user intervention.
"""
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple


class DependencyChecker:
    """Check and auto-install missing dependencies."""
    
    PYTHON_PACKAGES = [
        'PySide6',
        'opencv-python',
        'rapidocr-onnxruntime',
        'pillow',
        'numpy',
        'keyboard',
    ]
    
    SYSTEM_PACKAGES = {
        'ubuntu': ['spectacle', 'wl-clipboard', 'libxkbcommon0'],
        'debian': ['spectacle', 'wl-clipboard', 'libxkbcommon0'],
        'fedora': ['kde-applications-spectacle', 'wl-clipboard', 'libxkbcommon'],
        'arch': ['spectacle', 'wl-clipboard', 'libxkbcommon'],
        'kali': ['spectacle', 'wl-clipboard', 'libxkbcommon0'],
    }
    
    def __init__(self):
        self.distro = self._detect_distro()
        self.needs_sudo = False
        
    def _detect_distro(self) -> str:
        """Detect Linux distribution."""
        try:
            # Try /etc/os-release first
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('ID='):
                        return line.split('=')[1].strip().strip('"')
        except:
            pass
        
        # Fallback to platform.linux_distribution (deprecated but works)
        try:
            return platform.linux_distribution()[0].lower()
        except:
            return 'ubuntu'  # Default fallback
    
    def check_python_package(self, package: str) -> bool:
        """Check if a Python package is installed."""
        try:
            __import__(package.replace('-', '_'))
            return True
        except ImportError:
            return False
    
    def check_system_package(self, package: str) -> bool:
        """Check if a system package is installed."""
        result = subprocess.run(
            ['which', package],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    
    def install_python_package(self, package: str) -> bool:
        """Install a Python package using pip."""
        try:
            print(f"[Setup] Installing Python package: {package}")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package, '-q'],
                capture_output=True,
                timeout=300
            )
            if result.returncode == 0:
                print(f"[Setup] ✓ {package} installed")
                return True
            else:
                print(f"[Setup] ✗ Failed to install {package}")
                print(result.stderr.decode())
                return False
        except subprocess.TimeoutExpired:
            print(f"[Setup] ✗ Installation timeout for {package}")
            return False
        except Exception as e:
            print(f"[Setup] ✗ Error installing {package}: {e}")
            return False
    
    def install_system_package(self, package: str) -> bool:
        """Install a system package using apt/dnf/pacman."""
        try:
            if self.distro in ['ubuntu', 'debian', 'kali']:
                cmd = ['apt-get', 'install', '-y', package]
            elif self.distro == 'fedora':
                cmd = ['dnf', 'install', '-y', package]
            elif self.distro == 'arch':
                cmd = ['pacman', '-S', '--noconfirm', package]
            else:
                print(f"[Setup] Unknown distro: {self.distro}, skipping system package")
                return False
            
            print(f"[Setup] Installing system package: {package}")
            result = subprocess.run(
                ['sudo'] + cmd,
                capture_output=True,
                timeout=300
            )
            if result.returncode == 0:
                print(f"[Setup] ✓ {package} installed")
                return True
            else:
                print(f"[Setup] Note: Could not install {package} (might already be present)")
                return True  # Don't fail if system package install fails
        except subprocess.TimeoutExpired:
            print(f"[Setup] ✗ Installation timeout for system package {package}")
            return True
        except Exception as e:
            print(f"[Setup] Note: {e}")
            return True  # Don't fail
    
    def check_and_setup(self) -> Tuple[bool, List[str]]:
        """
        Check all dependencies and auto-install missing ones.
        
        Returns:
            (success: bool, missing_packages: List[str])
        """
        missing_python = []
        missing_system = []
        
        print("[Setup] Checking Python packages...")
        for package in self.PYTHON_PACKAGES:
            if not self.check_python_package(package):
                print(f"[Setup] Missing: {package}")
                missing_python.append(package)
                # Try to install
                if not self.install_python_package(package):
                    print(f"[Setup] ✗ Could not install {package}")
        
        print("\n[Setup] Checking system packages...")
        system_packages = self.SYSTEM_PACKAGES.get(self.distro, [])
        for package in system_packages:
            if not self.check_system_package(package):
                print(f"[Setup] Missing: {package}")
                missing_system.append(package)
                # Try to install with sudo
                self.install_system_package(package)
        
        # Final check
        all_found = True
        remaining = []
        for package in self.PYTHON_PACKAGES:
            if not self.check_python_package(package):
                all_found = False
                remaining.append(package)
        
        if all_found:
            print("\n[Setup] ✓ All dependencies ready!\n")
            return True, []
        else:
            print(f"\n[Setup] ✗ Could not install: {remaining}\n")
            return False, remaining


def ensure_dependencies():
    """Ensure all dependencies are available, exit if critical ones missing."""
    checker = DependencyChecker()
    success, missing = checker.check_and_setup()
    
    if not success:
        print("=" * 60)
        print("ERROR: Missing critical Python packages:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nManual installation:")
        print(f"  pip install {' '.join(missing)}")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    ensure_dependencies()
    print("Environment check passed!")
