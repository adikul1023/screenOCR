"""
Main application entry point for Wayland OCR utility.
Replicates Windows PowerToys Text Extractor for Linux.
"""
import sys
import os
import signal
from typing import Optional, Tuple
from threading import Thread
from pathlib import Path

# Auto-setup dependencies before importing
def _setup_dependencies():
    """Auto-setup missing dependencies on first run."""
    try:
        from setup_environment import ensure_dependencies
        ensure_dependencies()
    except ImportError:
        # setup_environment not available, try manual import
        missing = []
        for pkg in ['PySide6', 'opencv-python', 'rapidocr-onnxruntime', 'pillow', 'numpy', 'keyboard']:
            try:
                __import__(pkg.replace('-', '_'))
            except ImportError:
                missing.append(pkg)
        
        if missing:
            print("ERROR: Missing Python packages:")
            for pkg in missing:
                print(f"  - {pkg}")
            print("\nInstalling automatically...")
            import subprocess
            for pkg in missing:
                subprocess.run([sys.executable, '-m', 'pip', 'install', pkg, '-q'])
    except Exception as e:
        print(f"Warning: Setup error: {e}")

_setup_dependencies()

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer
    from PySide6.QtGui import QKeySequence, QGuiApplication
except ImportError as e:
    print(f"ERROR: Cannot import PySide6: {e}")
    print("This is a required dependency. Installation may have failed.")
    sys.exit(1)

try:
    from overlay import SelectionOverlay
    from portal import PortalScreenshot
    from ocr_engine import OCREngine
    from utils import clean_ocr_text
except ImportError as e:
    print(f"ERROR: Cannot import ScreenOCR modules: {e}")
    sys.exit(1)


def cli_main() -> int:
    """
    CLI entry point for console_scripts.
    Handles daemon and manual trigger commands.
    
    Returns:
        Exit code
    """
    import hotkey_daemon
    
    def print_usage() -> None:
        """Print command line usage."""
        import sys
        import os
        
        cmd = os.path.basename(sys.argv[0])
        
        print(f"\nScreenOCR - Hotkey-triggered OCR utility\n")
        print(f"Usage:")
        print(f"  {cmd} trigger          - Manually trigger OCR region selection")
        print(f"  {cmd} daemon start     - Start the hotkey listener daemon")
        print(f"  {cmd} daemon stop      - Stop the running daemon")
        print(f"  {cmd} daemon status    - Check daemon status\n")
        print(f"Hotkey: Super+Shift+T (customizable)\n")
        print(f"Examples:")
        print(f"  {cmd} daemon start 'ctrl+shift+c'")
        print(f"  {cmd} trigger\n")
    
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h', 'help'):
        print_usage()
        return 0
    
    command = sys.argv[1]
    
    if command == 'trigger':
        # Direct trigger mode
        return main_gui_trigger()
    
    elif command == 'daemon':
        if len(sys.argv) < 3:
            print("Usage: screenocr daemon [start|stop|status]")
            return 1
        
        subcommand = sys.argv[2]
        
        if subcommand == 'start':
            hotkey = sys.argv[3] if len(sys.argv) > 3 else None
            return hotkey_daemon.daemon_start(hotkey=hotkey)
        
        elif subcommand == 'stop':
            return hotkey_daemon.daemon_stop()
        
        elif subcommand == 'status':
            return hotkey_daemon.daemon_status()
        
        else:
            print(f"Unknown daemon command: {subcommand}")
            return 1
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'screenocr --help' for usage information")
        return 1



class OCRWorker(QObject):
    """
    Worker thread for OCR processing to avoid blocking UI.
    """
    finished = Signal()
    error = Signal(str)
    
    def __init__(
        self,
        screenshot_path: str,
        region: Tuple[int, int, int, int],
        ocr_engine: OCREngine
    ) -> None:
        """
        Initialize OCR worker.
        
        Args:
            screenshot_path: Path to screenshot file
            region: Selected region (x, y, width, height)
            ocr_engine: OCR engine instance
        """
        super().__init__()
        self.screenshot_path = screenshot_path
        self.region = region
        self.ocr_engine = ocr_engine
        self.text = ""
    
    def run(self) -> None:
        """Execute OCR processing."""
        try:
            print(f"Processing OCR for region: {self.region}")
            print(f"Screenshot path: {self.screenshot_path}")
            
            self.text = self.ocr_engine.extract_text(
                self.screenshot_path,
                self.region
            )
            
            print(f"OCR extracted text: '{self.text}'")
            
            # Copy to clipboard if text found
            if self.text.strip():
                clipboard = QApplication.clipboard()
                clipboard.setText(self.text)
                print(f"✓ Copied to clipboard: {len(self.text)} characters")
            else:
                print("⚠ No text extracted")
        except Exception as e:
            print(f"✗ OCR Error: {e}")
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class OcrApplication:
    """
    Main OCR application controller.
    """
    
    SHORTCUT_KEY = "Ctrl+Shift+T"
    
    def __init__(self) -> None:
        """Initialize OCR application."""
        self.app = QApplication.instance() or QApplication(sys.argv)
        
        # Setup signal handlers for Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Create timer to allow Python signal processing
        self.timer = QTimer()
        self.timer.start(500)  # Check every 500ms
        self.timer.timeout.connect(lambda: None)  # Wake up event loop
        
        self.ocr_engine = OCREngine()
        self.portal = PortalScreenshot()
        self.overlay: Optional[SelectionOverlay] = None
        self.ocr_worker_thread: Optional[QThread] = None
        self.should_exit = False
        
        # Check portal availability
        if not self.portal.is_available():
            self._show_error("Screenshot tool not available. Install spectacle, gnome-screenshot, or similar.")
            sys.exit(1)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C signal."""
        print("\n\nReceived Ctrl+C, exiting...")
        self.should_exit = True
        if self.overlay:
            self.overlay.close()
        QApplication.quit()
        sys.exit(0)
    
    def _setup_global_shortcut(self) -> bool:
        """
        Register global keyboard shortcut.
        
        Note: PySide6 doesn't have built-in global hotkey support on Linux.
        This uses external tool integration. For production, consider:
        - Using python-xlib (X11 only, not suitable for Wayland)
        - Using dbus with systemd user session
        - Using D-Bus method calls
        
        For now, we use a placeholder that should be replaced with
        actual DBus hotkey registration or system integration.
        
        Returns:
            True if setup succeeded
        """
        try:
            # Attempt to register hotkey via session bus
            # This is a simplified approach - production should use dedicated hotkey daemon
            import pydbus
            bus = pydbus.SessionBus()
            
            # For a complete implementation, register with GNOME Settings Daemon
            # or KDE Global Shortcuts. This is left as extensible hook.
            return True
        except Exception:
            return False
    
    def _show_error(self, message: str) -> None:
        """
        Show error dialog.
        
        Args:
            message: Error message
        """
        QMessageBox.critical(None, "OCR Error", message)
    
    def _show_info(self, message: str) -> None:
        """
        Show info dialog.
        
        Args:
            message: Info message
        """
        QMessageBox.information(None, "OCR", message)
    
    def _copy_to_clipboard(self, text: str) -> None:
        """
        Copy text to clipboard with Wayland compatibility.
        
        Args:
            text: Text to copy
        """
        # Method 1: wl-copy for Wayland (primary method)
        try:
            import subprocess
            # Use Popen to run wl-copy in background
            process = subprocess.Popen(
                ['wl-copy', '--type', 'text/plain'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            process.communicate(input=text.encode('utf-8'), timeout=2)
            if process.returncode == 0:
                print("[Clipboard] wl-copy successful")
                return
        except subprocess.TimeoutExpired:
            # wl-copy is running in background, this is normal
            print("[Clipboard] wl-copy started (background)")
            return
        except FileNotFoundError:
            print("[Clipboard] wl-copy not found, trying Qt clipboard")
        except Exception as e:
            print(f"[Clipboard] wl-copy failed: {e}")
        
        # Method 2: Qt clipboard fallback
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(text, mode=clipboard.Mode.Clipboard)
            clipboard.setText(text, mode=clipboard.Mode.Selection)
            # Force event processing to sync clipboard
            QApplication.processEvents()
            print("[Clipboard] Qt clipboard updated")
        except Exception as e:
            print(f"[Clipboard] Qt clipboard failed: {e}")
    
    def _on_overlay_region_selected(self, region: Tuple[int, int, int, int]) -> None:
        """
        Handle region selection from overlay.
        
        Args:
            region: Selected region (x, y, width, height)
        """
        try:
            print(f"\n=== OCR Process Started ===")
            print(f"Selected region: {region}")
            
            # Capture screenshot via portal
            print("Capturing screenshot...")
            screenshot_path = self.portal.capture_screen()
            if not screenshot_path:
                print("✗ Screenshot capture failed")
                self._show_error("Failed to capture screenshot.")
                return
            
            print(f"✓ Screenshot saved: {screenshot_path}")
            
            # Process OCR directly (synchronous)
            print("Running OCR...")
            text = self.ocr_engine.extract_text(screenshot_path, region)
            
            print("\n==== OCR Result ====")
            print(text)
            print("====================\n")
            
            if text.strip():
                # Copy to clipboard - Wayland compatible
                self._copy_to_clipboard(text)
                line_count = len(text.split('\n'))
                print(f"✓ Copied {len(text)} characters ({line_count} lines) to clipboard")
                print(f"=== OCR Complete ===\n")
            else:
                print("⚠ No text extracted")
                print(f"=== OCR Complete (no text) ===\n")
            
            # Delay exit to ensure clipboard is synced (Wayland requirement)
            QTimer.singleShot(500, QApplication.quit)
                
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            self._show_error(f"Unexpected error: {str(e)}")
            QTimer.singleShot(100, QApplication.quit)
    
    def _process_ocr(
        self,
        screenshot_path: str,
        region: Tuple[int, int, int, int]
    ) -> None:
        """
        Process OCR in background thread.
        
        Args:
            screenshot_path: Path to captured screenshot
            region: Selected region tuple
        """
        print("Starting OCR worker thread...")
        
        # Create worker
        worker = OCRWorker(screenshot_path, region, self.ocr_engine)
        
        # Create thread
        self.ocr_worker_thread = QThread()
        worker.moveToThread(self.ocr_worker_thread)
        
        # Connect signals
        self.ocr_worker_thread.started.connect(worker.run)
        worker.finished.connect(self.ocr_worker_thread.quit)
        worker.finished.connect(self._on_ocr_finished)
        worker.error.connect(self._on_ocr_error)
        
        # Start
        print("Launching OCR thread...")
        self.ocr_worker_thread.start()
        print("OCR thread started")
    
    def _on_ocr_finished(self) -> None:
        """Handle OCR completion."""
        # Cleanup thread
        if self.ocr_worker_thread:
            self.ocr_worker_thread.deleteLater()
            self.ocr_worker_thread = None
    
    def _on_ocr_error(self, error: str) -> None:
        """
        Handle OCR error.
        
        Args:
            error: Error message
        """
        self._show_error(f"OCR processing failed: {error}")
    
    def _trigger_wayland_native(self) -> None:
        """Use native desktop environment tools for region capture."""
        import subprocess
        import tempfile
        import os
        import shutil
        
        try:
            # Create temp file for screenshot
            fd, temp_path = tempfile.mkstemp(suffix='.png')
            os.close(fd)
            
            captured = False
            
            # Detect Desktop Environment to avoid running incompatible tools
            current_desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').upper()
            
            # Check for KDE Spectacle
            if 'KDE' in current_desktop and shutil.which('spectacle'):
                # -r (region), -b (background), -n (no notify), -o (output)
                if subprocess.run(['spectacle', '-r', '-b', '-n', '-o', temp_path]).returncode == 0:
                    captured = True
                    
            # Check for GNOME Screenshot
            elif 'GNOME' in current_desktop and shutil.which('gnome-screenshot'):
                # -a (area), -f (file)
                if subprocess.run(['gnome-screenshot', '-a', '-f', temp_path]).returncode == 0:
                    captured = True
                    
            # Check for slurp/grim (wlroots / Hyprland / Sway)
            elif shutil.which('slurp') and shutil.which('grim'):
                slurp_process = subprocess.run(['slurp'], capture_output=True, text=True)
                if slurp_process.returncode == 0:
                    selection = slurp_process.stdout.strip()
                    if subprocess.run(['grim', '-g', selection, temp_path]).returncode == 0:
                        captured = True
            
            # Fallbacks if the specific DE tool failed or wasn't found
            if not captured and shutil.which('flameshot'):
                with open(temp_path, 'wb') as f:
                    if subprocess.run(['flameshot', 'gui', '-r'], stdout=f).returncode == 0:
                        captured = True
            
            if not captured and shutil.which('scrot'):
                if subprocess.run(['scrot', '-s', temp_path]).returncode == 0:
                    captured = True
                    
            if not captured or not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                print("Screenshot cancelled or no compatible tool found.")
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                QTimer.singleShot(100, QApplication.quit)
                return
                
            print(f"Captured screenshot to {temp_path}")
            print("Processing OCR...")
            
            # Process OCR directly (synchronous)
            text = self.ocr_engine.extract_text(temp_path, None)
            
            if not text:
                print("No text could be extracted.")
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return
                
            self._copy_to_clipboard(text)
            
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
            print("\n=== OCR Process Complete ===")
            print(f"Extracted {len(text)} characters")
            print("Text copied to clipboard!")
            
            # Allow time for clipboard to sync before quitting
            QTimer.singleShot(500, QApplication.quit)
            
        except Exception as e:
            self._show_error(f"Native capture failed: {str(e)}")

    def trigger_ocr(self) -> None:
        """
        Trigger OCR workflow on hotkey press.
        
        This is called when user presses the global shortcut.
        """
        import os
        # Check if running on Wayland
        wayland_display = os.environ.get('WAYLAND_DISPLAY')
        if wayland_display:
            self._trigger_wayland_native()
        else:
            try:
                # Show selection overlay
                self.overlay = SelectionOverlay()
                self.overlay.region_selected.connect(self._on_overlay_region_selected)
                self.overlay.cancelled.connect(self._on_overlay_cancelled)
                self.overlay.showFullScreen()
            except Exception as e:
                self._show_error(f"Failed to show selection overlay: {str(e)}")
    
    def _on_overlay_cancelled(self) -> None:
        """Handle overlay cancellation."""
        print("\nOCR cancelled, exiting...")
        QTimer.singleShot(100, QApplication.quit)
    
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            Application exit code
        """
        # Support old-style 'python main.py trigger' command for backwards compatibility
        if len(sys.argv) > 1 and sys.argv[1] == 'trigger':
            self.trigger_ocr()
            return self.app.exec()
        else:
            # In daemon mode, would need to listen for hotkey.
            # For GUI mode, show info
            self._show_info(
                "OCR utility ready.\n\n"
                "For daemon mode with global hotkeys:\n"
                "  screenocr daemon start\n\n"
                "For manual testing:\n"
                "  screenocr trigger"
            )
            return 0
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.ocr_worker_thread and self.ocr_worker_thread.isRunning():
            self.ocr_worker_thread.quit()
            self.ocr_worker_thread.wait()
        
        if self.ocr_engine:
            self.ocr_engine.cleanup()
        
        if self.portal:
            self.portal.cleanup()


def main_gui_trigger() -> int:
    """
    Main entry point for GUI trigger (hotkey daemon calls this).
    
    Returns:
        Exit code
    """
    app = OcrApplication()
    try:
        app.trigger_ocr()
        return app.app.exec()
    finally:
        app.cleanup()



def main() -> int:
    """
    Main entry point for direct execution.
    
    Returns:
        Exit code
    """
    return cli_main()


if __name__ == '__main__':
    sys.exit(main())
