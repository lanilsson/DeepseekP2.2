"""
Login Screen Module - Implements a stylish login/splash screen

This module contains the LoginScreen class which provides a dark mode
diffusing effect with centered "Jordan AI" text before launching the main application.
"""

import sys
import time
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, pyqtProperty, QRect
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect, QSizePolicy
from PyQt6.QtGui import QFont, QColor, QPalette, QLinearGradient, QPainter, QBrush, QRadialGradient, QPen

class LoginScreen(QWidget):
    """A stylish login/splash screen with diffusing effect and centered text."""
    
    def __init__(self, on_complete_callback=None):
        super().__init__(None)  # No parent to ensure it's a top-level window
        self.on_complete_callback = on_complete_callback
        self._opacity = 0.0
        self._text_opacity = 0.0
        
        # Set window properties
        self.setWindowTitle("Jordan AI")
        self.resize(800, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Set up the UI
        self.setup_ui()
        
        # Start animations after a short delay to ensure window is visible
        QTimer.singleShot(100, self.start_animations)
        
    def setup_ui(self):
        """Set up the login screen UI."""
        # Create title label with large, modern font
        self.title_label = QLabel("JORDAN AI", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFont(QFont("Helvetica", 72, QFont.Weight.Light))
        self.title_label.setStyleSheet("""
            color: #FFFFFF;
            background-color: transparent;
            letter-spacing: 5px;
            text-transform: uppercase;
        """)
        
        # Make sure the label is centered and sized appropriately
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Create opacity effect for the title
        self.title_opacity_effect = QGraphicsOpacityEffect(self.title_label)
        self.title_opacity_effect.setOpacity(0)
        self.title_label.setGraphicsEffect(self.title_opacity_effect)
        
        # Position the title in the center
        self.title_label.setGeometry(0, 0, self.width(), self.height())
    
    def resizeEvent(self, event):
        """Handle resize events to keep the title centered."""
        super().resizeEvent(event)
        self.title_label.setGeometry(0, 0, self.width(), self.height())
    
    def paintEvent(self, event):
        """Custom paint event to create the diffusing dark background effect."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill the entire window with a dark background
        painter.fillRect(self.rect(), QColor(18, 18, 18))
        
        # Create a radial gradient for the diffusing effect
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # Main diffusing gradient - more modern dark theme colors
        gradient = QRadialGradient(center_x, center_y, self.width() * 0.8)
        gradient.setColorAt(0, QColor(45, 45, 60, int(255 * self._opacity)))
        gradient.setColorAt(0.4, QColor(30, 30, 45, int(230 * self._opacity)))
        gradient.setColorAt(0.7, QColor(25, 25, 35, int(180 * self._opacity)))
        gradient.setColorAt(1, QColor(18, 18, 18, int(100 * self._opacity)))
        
        painter.fillRect(self.rect(), QBrush(gradient))
        
        # Add subtle particle effects (small dots) with more modern colors
        painter.setPen(QPen(QColor(120, 120, 180, int(80 * self._opacity)), 1.5))
        for i in range(40):
            x = center_x + (i * 37 + self.width() / 3) % self.width() - self.width() / 2
            y = center_y + (i * 23 + self.height() / 3) % self.height() - self.height() / 2
            size = 2 + (i % 4)
            painter.drawEllipse(int(x), int(y), size, size)
    
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.update()  # Trigger a repaint
    
    @pyqtProperty(float)
    def text_opacity(self):
        return self._text_opacity
    
    @text_opacity.setter
    def text_opacity(self, value):
        self._text_opacity = value
        self.title_opacity_effect.setOpacity(value)
        self.update()  # Trigger a repaint
    
    def start_animations(self):
        """Start the login screen animations."""
        # Background diffusion animation
        self.bg_animation = QPropertyAnimation(self, b"opacity")
        self.bg_animation.setDuration(2000)
        self.bg_animation.setStartValue(0.0)
        self.bg_animation.setEndValue(1.0)
        self.bg_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Title opacity animation (delayed start)
        self.title_animation = QPropertyAnimation(self, b"text_opacity")
        self.title_animation.setDuration(1500)
        self.title_animation.setStartValue(0.0)
        self.title_animation.setEndValue(1.0)
        self.title_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Start background animation immediately
        self.bg_animation.start()
        
        # Start title animation after a delay
        QTimer.singleShot(800, self.title_animation.start)
        
        # Set timer to close the login screen after animations
        QTimer.singleShot(3500, self.finish_login)
    
    def finish_login(self):
        """Complete the login process and call the callback."""
        if self.on_complete_callback:
            self.on_complete_callback()
        self.close()

def show_login_screen(callback=None):
    """Show the login screen and call the callback when complete."""
    login_screen = LoginScreen(callback)
    login_screen.show()
    return login_screen

if __name__ == "__main__":
    # Test the login screen
    app = QApplication(sys.argv)
    login = show_login_screen(lambda: print("Login complete!"))
    sys.exit(app.exec())