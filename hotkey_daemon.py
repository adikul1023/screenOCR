"""
Global hotkey listener daemon for OCR utility.
Runs in background and triggers OCR on hotkey press.
"""
import sys
import os
import time
import signal
import json
from pathlib import Path
from typing import Callable, Optional
from threading import Thread, Event
import subprocess

try:
    import keyboard
except ImportError:
    print("Error: 'keyboard' package not found. Install with: pip install keyboard")
    print("Note: This requires root privileges or proper udev rules on Linux.")
    sys.exit(1)


class HotkeyDaemon:
    """
    Daemon that listens for global hotkeys and triggers OCR.
    """
    
    # Configuration
    CONFIG_DIR = Path.home() / '.config' / 'screenocr'
    CONFIG_FILE = CONFIG_DIR / 'config.json'
    PID_FILE = CONFIG_DIR / 'daemon.pid'
    
    # Default hotkey: Super+Shift+T
    DEFAULT_HOTKEY = 'super+shift+t'
    
    def __init__(self, hotkey: Optional[str] = None) -> None:
        """
        Initialize hotkey daemon.
        
        Args:
            hotkey: Hotkey combination (e.g., 'super+shift+t', 'ctrl+alt+o')
        """
        self.hotkey = hotkey or self.DEFAULT_HOTKEY
        self.running = False
        self.stop_event = Event()
        
        # Create config directory if needed
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Setup signal handling
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle termination signals."""
        print("\n[Daemon] Received shutdown signal, stopping...")
        self.stop()
    
    def _save_pid(self) -> None:
        """Save daemon PID to file."""
        try:
            self.PID_FILE.write_text(str(os.getpid()))
            print(f"[Daemon] PID saved to {self.PID_FILE}")
        except Exception as e:
            print(f"[Daemon] Warning: Could not save PID: {e}")
    
    def _remove_pid(self) -> None:
        """Remove PID file."""
        try:
            if self.PID_FILE.exists():
                self.PID_FILE.unlink()
        except Exception as e:
            print(f"[Daemon] Warning: Could not remove PID file: {e}")
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            config = {
                'hotkey': self.hotkey,
                'version': '1.0',
                'launched': time.time()
            }
            self.CONFIG_FILE.write_text(json.dumps(config, indent=2))
            print(f"[Daemon] Config saved to {self.CONFIG_FILE}")
        except Exception as e:
            print(f"[Daemon] Warning: Could not save config: {e}")
    
    def _trigger_ocr(self) -> None:
        """
        Trigger the OCR process.
        Called when hotkey is pressed.
        """
        print(f"\n[Hotkey] {self.hotkey.upper()} pressed - Triggering OCR...")
        
        try:
            # Get the directory where this script is located
            script_dir = Path(__file__).parent
            
            # Run main.py with trigger argument
            cmd = [
                sys.executable,
                str(script_dir / 'main.py'),
                'trigger'
            ]
            
            print(f"[Daemon] Executing: {' '.join(cmd)}")
            
            # Run OCR in subprocess (don't block daemon)
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # Start in new process group (detach from daemon)
            )
            
            print("[Daemon] OCR process started successfully")
            
        except Exception as e:
            print(f"[Daemon] Error triggering OCR: {e}")
            import traceback
            traceback.print_exc()
    
    def _register_hotkey(self) -> bool:
        """
        Register the global hotkey listener.
        
        Returns:
            True if successful
        """
        try:
            print(f"[Daemon] Registering hotkey: {self.hotkey}")
            keyboard.add_hotkey(self.hotkey, self._trigger_ocr, suppress=False)
            print(f"[Daemon] ✓ Hotkey '{self.hotkey}' registered successfully")
            return True
        except Exception as e:
            print(f"[Daemon] ✗ Failed to register hotkey: {e}")
            print("\n[Daemon] Hotkey registration requires elevated privileges.")
            print("[Daemon] You can either:")
            print("  1. Run this program with sudo")
            print("  2. Add udev rules to allow keyboard input (advanced)")
            print("  3. Run under a display manager that supports hotkeys (GNOME, KDE)")
            return False
    
    def start(self) -> bool:
        """
        Start the hotkey listener daemon.
        
        Returns:
            True if started successfully
        """
        if self.running:
            print("[Daemon] Already running")
            return True
        
        print(f"\n[Daemon] ScreenOCR Hotkey Daemon Starting...")
        print(f"[Daemon] Python: {sys.executable}")
        print(f"[Daemon] Hotkey: {self.hotkey}")
        print(f"[Daemon] Config: {self.CONFIG_FILE}")
        
        # Save PID and config
        self._save_pid()
        self._save_config()
        
        # Register hotkey
        if not self._register_hotkey():
            self._remove_pid()
            return False
        
        self.running = True
        print("[Daemon] ✓ Daemon started successfully")
        print(f"[Daemon] Press '{self.hotkey.upper()}' to trigger OCR")
        print("[Daemon] Press Ctrl+C to stop\n")
        
        return True
    
    def stop(self) -> None:
        """Stop the hotkey listener daemon."""
        if not self.running:
            return
        
        print("\n[Daemon] Stopping...")
        self.running = False
        self.stop_event.set()
        
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        
        self._remove_pid()
        print("[Daemon] ✓ Stopped")
    
    def run(self) -> int:
        """
        Run the daemon (blocking).
        
        Returns:
            Exit code
        """
        if not self.start():
            return 1
        
        try:
            # Keep daemon running by listening to keyboard events
            keyboard.wait(hotkey=None)  # Wait indefinitely for any keyboard event
        except KeyboardInterrupt:
            self.stop()
            return 0
        except Exception as e:
            print(f"[Daemon] Error: {e}")
            self.stop()
            return 1
        
        return 0
    
    @staticmethod
    def get_running_daemon_pid() -> Optional[int]:
        """
        Get PID of running daemon, if any.
        
        Returns:
            PID if daemon is running, None otherwise
        """
        pid_file = HotkeyDaemon.PID_FILE
        
        if not pid_file.exists():
            return None
        
        try:
            pid = int(pid_file.read_text().strip())
            
            # Check if process is actually running
            if os.path.exists(f'/proc/{pid}'):
                return pid
            else:
                # Stale PID file
                pid_file.unlink()
                return None
        except (ValueError, OSError):
            return None
    
    @staticmethod
    def is_daemon_running() -> bool:
        """Check if daemon is currently running."""
        return HotkeyDaemon.get_running_daemon_pid() is not None


def daemon_start(hotkey: Optional[str] = None) -> int:
    """
    Start the hotkey daemon.
    
    Args:
        hotkey: Optional hotkey configuration
        
    Returns:
        Exit code
    """
    if HotkeyDaemon.is_daemon_running():
        print("✗ Daemon already running (PID: {})".format(
            HotkeyDaemon.get_running_daemon_pid()
        ))
        return 1
    
    daemon = HotkeyDaemon(hotkey=hotkey)
    return daemon.run()


def daemon_stop() -> int:
    """
    Stop the hotkey daemon.
    
    Returns:
        Exit code
    """
    pid = HotkeyDaemon.get_running_daemon_pid()
    
    if pid is None:
        print("✗ Daemon is not running")
        return 1
    
    try:
        print(f"Stopping daemon (PID: {pid})...")
        os.kill(pid, signal.SIGTERM)
        
        # Wait a bit for graceful shutdown
        time.sleep(1)
        
        # Check if still running
        if HotkeyDaemon.is_daemon_running():
            print("Force killing daemon...")
            os.kill(pid, signal.SIGKILL)
        
        print("✓ Daemon stopped")
        return 0
    except ProcessLookupError:
        print("✓ Daemon already stopped")
        HotkeyDaemon.PID_FILE.unlink(missing_ok=True)
        return 0
    except Exception as e:
        print(f"✗ Error stopping daemon: {e}")
        return 1


def daemon_status() -> int:
    """
    Show daemon status.
    
    Returns:
        Exit code
    """
    if HotkeyDaemon.is_daemon_running():
        pid = HotkeyDaemon.get_running_daemon_pid()
        print(f"✓ Daemon is running (PID: {pid})")
        
        # Try to read config
        if HotkeyDaemon.CONFIG_FILE.exists():
            try:
                config = json.loads(HotkeyDaemon.CONFIG_FILE.read_text())
                print(f"  Hotkey: {config.get('hotkey', 'unknown')}")
            except Exception:
                pass
        
        return 0
    else:
        print("✗ Daemon is not running")
        return 1


if __name__ == '__main__':
    err_code = daemon_start()
    sys.exit(err_code)
