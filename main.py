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

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer
from PySide6.QtGui import QKeySequence, QGuiApplication

from overlay import SelectionOverlay
from portal import PortalScreenshot
from ocr_engine import OCREngine
from utils import clean_ocr_text


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
    
    def trigger_ocr(self) -> None:
        """
        Trigger OCR workflow on hotkey press.
        
        This is called when user presses the global shortcut.
        """
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
        # For development/testing: show info and wait for trigger
        # In production, this would register global hotkey and block until exit
        
        # Simplified entry point - would need system integration for true global hotkey
        # Options for production:
        # 1. Use KDE's org.kde.kglobalshortcuts D-Bus interface
        # 2. Use GNOME's media keys via settings daemon
        # 3. Integrate with systemd user session events
        # 4. Use python-evdev directly (requires udev rules)
        
        # For now, provide command-line trigger or show usage
        if len(sys.argv) > 1 and sys.argv[1] == 'trigger':
            self.trigger_ocr()
            return self.app.exec()
        else:
            self._show_info(
                "OCR utility ready.\n\n"
                "Global hotkey support requires system integration.\n\n"
                "For testing, run: python main.py trigger"
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


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    app = OcrApplication()
    try:
        return app.run()
    finally:
        app.cleanup()


if __name__ == '__main__':
    sys.exit(main())
