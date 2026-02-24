"""
Fullscreen transparent overlay for region selection.
"""
from typing import Tuple, Optional
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, Signal, QPoint, QRect, QSize, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush


class SelectionOverlay(QWidget):
    """
    Fullscreen transparent overlay for region selection via mouse drag.
    """
    
    # Signal emitted when region is selected: (x, y, width, height)
    region_selected = Signal(tuple)
    # Signal emitted when overlay is cancelled
    cancelled = Signal()
    
    def __init__(self) -> None:
        """Initialize overlay widget."""
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        # Track selection rectangle
        self.start_point: Optional[QPoint] = None
        self.end_point: Optional[QPoint] = None
        self.selecting = False
        self.region_emitted = False  # Track if region was successfully selected
        
        # Make fullscreen
        self.setGeometry(QApplication.primaryScreen().geometry())
    
    def mousePressEvent(self, event) -> None:
        """
        Handle mouse press to start selection.
        
        Args:
            event: Mouse event
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.globalPosition().toPoint()
            self.end_point = self.start_point
            self.selecting = True
            self.update()
    
    def mouseMoveEvent(self, event) -> None:
        """
        Handle mouse move to update selection rectangle.
        
        Args:
            event: Mouse event
        """
        if self.selecting:
            self.end_point = event.globalPosition().toPoint()
            self.update()
    
    def mouseReleaseEvent(self, event) -> None:
        """
        Handle mouse release to finalize selection.
        
        Args:
            event: Mouse event
        """
        if event.button() == Qt.MouseButton.LeftButton and self.selecting:
            self.selecting = False
            
            if self.start_point and self.end_point:
                # Calculate region
                x1 = min(self.start_point.x(), self.end_point.x())
                y1 = min(self.start_point.y(), self.end_point.y())
                x2 = max(self.start_point.x(), self.end_point.x())
                y2 = max(self.start_point.y(), self.end_point.y())
                
                width = x2 - x1
                height = y2 - y1
                
                # Only emit if region has meaningful size
                if width > 10 and height > 10:
                    self.region_emitted = True
                    self.region_selected.emit((x1, y1, width, height))
            
            # Close overlay
            self.close()
    
    def keyPressEvent(self, event) -> None:
        """
        Handle key press (Escape to cancel).
        
        Args:
            event: Key event
        """
        if event.key() == Qt.Key.Key_Escape:
            print("\nOverlay cancelled by user (Escape)")
            self.close()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event) -> None:
        """
        Handle overlay close event.
        
        Args:
            event: Close event
        """
        if not self.region_emitted:
            # User cancelled without selecting
            QTimer.singleShot(0, self.cancelled.emit)
        super().closeEvent(event)
    
    def paintEvent(self, event) -> None:
        """
        Paint overlay with selection rectangle and dimmed background.
        
        Args:
            event: Paint event
        """
        painter = QPainter(self)
        
        # Semi-transparent dark background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 64))
        
        # Draw selection rectangle if active
        if self.selecting and self.start_point and self.end_point:
            # Calculate rectangle
            rect = QRect(self.start_point, self.end_point).normalized()
            
            # Erase (make transparent) the selected area
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_Clear
            )
            painter.fillRect(rect, QColor(0, 0, 0, 0))
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            
            # Draw rectangle border
            pen = QPen(QColor(100, 200, 255), 2)
            painter.setPen(pen)
            painter.drawRect(rect)
        
        painter.end()
    
    def show_and_wait(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Show overlay and wait for selection.
        
        Returns:
            Selected region (x, y, width, height) or None if cancelled
        """
        self.region = None
        self.region_selected.connect(self._on_region_selected)
        self.showFullScreen()
        self.setFocus()
        
        # This will be handled via signal, but we return region if set
        return None
    
    def _on_region_selected(self, region: Tuple[int, int, int, int]) -> None:
        """
        Handle region selection signal.
        
        Args:
            region: Selected region tuple
        """
        self.region = region
