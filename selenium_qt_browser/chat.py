"""
Chat Module - Implements AI chat functionality

This module contains the AIChatTab class which provides a UI for
communicating with two AI assistants in a chatroom-like interface.
"""

import os
import sys
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QSplitter, QComboBox, QScrollArea,
    QFrame
)
from PyQt6.QtGui import QFont, QTextCursor, QColor

class ChatMessage(QFrame):
    """A single chat message widget."""
    
    def __init__(self, sender, message, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        # Set background and text color based on sender
        if sender == "User":
            self.setStyleSheet("background-color: #e6f7ff; color: #000000; border-radius: 5px; padding: 5px;")
        elif sender == "AI 1":
            self.setStyleSheet("background-color: #404040; color: #ffffff; border-radius: 5px; padding: 5px;")
        elif sender == "AI 2":
            self.setStyleSheet("background-color: #004000; color: #ffffff; border-radius: 5px; padding: 5px;")
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add sender and timestamp
        header_layout = QHBoxLayout()
        
        # Create sender label with explicit styling
        sender_label = QLabel(sender)
        sender_label.setStyleSheet("font-weight: bold;")
        
        # Create timestamp with explicit styling
        timestamp = QLabel(datetime.now().strftime('%H:%M:%S'))
        timestamp.setStyleSheet("font-size: 9pt;")
        timestamp.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        header_layout.addWidget(sender_label)
        header_layout.addWidget(timestamp)
        layout.addLayout(header_layout)
        
        # Add message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.TextFormat.PlainText)  # Use plain text to avoid HTML formatting issues
        layout.addWidget(message_label)

class AIChatTab(QWidget):
    """A tab for communicating with two AI assistants."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
        # Initialize with a welcome message
        self.add_message("AI 1", "Hello! I'm AI Assistant 1. How can I help you today?")
        self.add_message("AI 2", "Hi there! I'm AI Assistant 2. Feel free to ask me anything!")
    
    def setup_ui(self):
        """Set up the chat UI."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create chat area
        self.chat_area = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_area)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(10)
        
        # Create scroll area for chat
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.chat_area)
        
        # Create input area
        input_layout = QHBoxLayout()
        
        # AI selector
        self.ai_selector = QComboBox()
        self.ai_selector.addItems(["Both AIs", "AI 1", "AI 2"])
        input_layout.addWidget(self.ai_selector)
        
        # Message input
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        # Send button
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        # Add components to main layout
        main_layout.addWidget(scroll_area)
        main_layout.addLayout(input_layout)
    
    def add_message(self, sender, message):
        """Add a message to the chat area."""
        message_widget = ChatMessage(sender, message, self)
        self.chat_layout.addWidget(message_widget)
        
        # Scroll to the bottom
        QTimer.singleShot(100, lambda: self.parent.scroll_to_bottom(self.chat_area))
    
    def send_message(self):
        """Send a user message and get AI responses."""
        message = self.message_input.text().strip()
        if not message:
            return
        
        # Add user message
        self.add_message("User", message)
        self.message_input.clear()
        
        # Get selected AI
        selected_ai = self.ai_selector.currentText()
        
        # Simulate AI responses (in a real app, this would call an AI API)
        QTimer.singleShot(500, lambda: self.simulate_ai_response(message, selected_ai))
    
    def simulate_ai_response(self, user_message, selected_ai):
        """Simulate responses from the AIs."""
        if selected_ai in ["Both AIs", "AI 1"]:
            response1 = f"AI 1 response to: {user_message}"
            self.add_message("AI 1", response1)
        
        if selected_ai in ["Both AIs", "AI 2"]:
            # Add a slight delay between responses
            QTimer.singleShot(800, lambda: self.add_message("AI 2", f"AI 2 response to: {user_message}"))