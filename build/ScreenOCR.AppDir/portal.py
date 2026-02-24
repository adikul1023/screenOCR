"""
XDG Desktop Portal integration for Wayland screenshot functionality.
"""
import os
import tempfile
import subprocess
from typing import Optional
from pathlib import Path
from urllib.parse import urlparse, unquote


class PortalScreenshot:
    """
    Handle screenshots via XDG Desktop Portal (Wayland-safe).
    Uses gnome-screenshot or spectacle as fallback for simplicity.
    """
    
    def __init__(self) -> None:
        """Initialize portal connection."""
        self.screenshot_tool = self._find_screenshot_tool()
    
    def _find_screenshot_tool(self) -> Optional[str]:
        """
        Find available screenshot tool.
        
        Returns:
            Path to screenshot tool or None
        """
        tools = ['gnome-screenshot', 'spectacle', 'flameshot', 'scrot']
        for tool in tools:
            try:
                result = subprocess.run(
                    ['which', tool],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode == 0:
                    return tool
            except Exception:
                continue
        return None
    
    def is_available(self) -> bool:
        """
        Check if screenshot portal is available.
        
        Returns:
            True if portal is available
        """
        return self.screenshot_tool is not None
    
    def capture_screen(self) -> Optional[str]:
        """
        Capture full screen using available screenshot tool.
        
        Returns:
            Path to screenshot file or None on failure
        """
        if not self.is_available():
            return None
        
        try:
            # Create temp file for screenshot
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.png',
                delete=False,
                dir=tempfile.gettempdir()
            )
            temp_path = temp_file.name
            temp_file.close()
            
            # Take screenshot based on available tool
            if self.screenshot_tool == 'gnome-screenshot':
                result = subprocess.run(
                    ['gnome-screenshot', '-f', temp_path],
                    capture_output=True,
                    timeout=5
                )
            elif self.screenshot_tool == 'spectacle':
                result = subprocess.run(
                    ['spectacle', '-b', '-n', '-o', temp_path],
                    capture_output=True,
                    timeout=5
                )
            elif self.screenshot_tool == 'flameshot':
                result = subprocess.run(
                    ['flameshot', 'full', '-p', temp_path],
                    capture_output=True,
                    timeout=5
                )
            elif self.screenshot_tool == 'scrot':
                result = subprocess.run(
                    ['scrot', temp_path],
                    capture_output=True,
                    timeout=5
                )
            else:
                return None
            
            if result.returncode == 0 and os.path.exists(temp_path):
                return temp_path
            
            # Cleanup on failure
            try:
                os.unlink(temp_path)
            except Exception:
                pass
            
            return None
        except Exception:
            return None
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        pass
