"""
NotePage Module - Implements note-taking functionality

This module contains the NotePage class which provides a UI for
creating and editing notes with simple Markdown-like formatting.
"""

from selenium_qt_browser.tab_types import TabType
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel
)
from PyQt6.QtGui import (
    QFont, QTextCursor, QColor, QTextCharFormat,
    QTextBlockFormat, QTextListFormat, QKeyEvent
)

class NotePage(QWidget):
    """A tab for creating and editing notes with simple Markdown-like formatting."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.tab_type = TabType.NOTEPAGE
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the note page UI."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create text editor with modern styling
        self.text_editor = MarkdownTextEdit(self)
        self.text_editor.setStyleSheet("""
            background-color: #1e1e1e;
            color: #f0f0f0;
            border: 1px solid #333333;
            border-radius: 6px;
            padding: 8px;
        """)
        self.text_editor.setFont(QFont("Courier New", 11))
        self.text_editor.setPlaceholderText("Start typing your notes here...")
        
        # Add text editor to main layout
        main_layout.addWidget(self.text_editor)
        
        # Add status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            color: #64FFDA;
            font-size: 10px;
        """)
        status_layout.addWidget(self.status_label)
        
        # Add word count
        self.word_count_label = QLabel("Words: 0")
        self.word_count_label.setStyleSheet("""
            color: #64FFDA;
            font-size: 10px;
        """)
        self.word_count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        status_layout.addWidget(self.word_count_label)
        
        main_layout.addLayout(status_layout)
        
        # Connect signals
        self.text_editor.textChanged.connect(self.update_word_count)
        
        # Set parent reference for the text editor
        self.text_editor.notepage = self
    
    def update_word_count(self):
        """Update the word count display."""
        text = self.text_editor.toPlainText()
        word_count = len(text.split()) if text else 0
        self.word_count_label.setText(f"Words: {word_count}")
    
    def update_status(self, message):
        """Update the status label."""
        self.status_label.setText(message)


class MarkdownTextEdit(QTextEdit):
    """A custom QTextEdit with Markdown formatting support."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notepage = None
        self.editing_block = False
        self.setAcceptRichText(True)
        
        # Store the original text for each block
        self.original_text = {}
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        # If Enter is pressed, apply Markdown formatting
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.apply_markdown_formatting()
            
        # Call the parent class implementation
        super().keyPressEvent(event)
    
    def apply_markdown_formatting(self):
        """Apply Markdown formatting to the current line."""
        if self.editing_block:
            return
            
        cursor = self.textCursor()
        block = cursor.block()
        text = block.text().strip()
        
        # Store the original text
        self.original_text[block.position()] = text
        
        # Apply formatting based on Markdown syntax
        if text.startswith("# "):
            # Header 1
            self.format_header(cursor, text[2:], 1)
            self.notepage.update_status("Header 1 formatted")
        elif text.startswith("## "):
            # Header 2
            self.format_header(cursor, text[3:], 2)
            self.notepage.update_status("Header 2 formatted")
        elif text.startswith("### "):
            # Header 3
            self.format_header(cursor, text[4:], 3)
            self.notepage.update_status("Header 3 formatted")
        elif text.startswith("- "):
            # Bullet list
            self.format_list_item(cursor, text[2:])
            self.notepage.update_status("List item formatted")
        elif "*" in text and text.count("*") >= 2:
            # Bold text
            self.format_bold(cursor, text)
            self.notepage.update_status("Bold text formatted")
        else:
            # No special formatting
            self.notepage.update_status("Ready")
    
    def format_header(self, cursor, text, level):
        """Format text as a header."""
        self.editing_block = True
        
        # Select the entire block
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        
        # Create format for header
        format = QTextCharFormat()
        if level == 1:
            format.setFontPointSize(18)
        elif level == 2:
            format.setFontPointSize(16)
        else:
            format.setFontPointSize(14)
        format.setFontWeight(QFont.Weight.Bold)
        
        # Apply the format
        cursor.setCharFormat(format)
        cursor.insertText(text)
        
        self.editing_block = False
    
    def format_list_item(self, cursor, text):
        """Format text as a list item."""
        self.editing_block = True
        
        # Select the entire block
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        
        # Create format for list item
        format = QTextCharFormat()
        
        # Apply the format
        cursor.setCharFormat(format)
        cursor.insertText("• " + text)
        
        self.editing_block = False
    
    def format_bold(self, cursor, text):
        """Format text with bold."""
        self.editing_block = True
        
        # Select the entire block
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        
        # Parse the text to find bold sections
        parts = []
        is_bold = False
        current_part = ""
        
        for char in text:
            if char == '*':
                if current_part:
                    parts.append((current_part, is_bold))
                    current_part = ""
                is_bold = not is_bold
            else:
                current_part += char
        
        if current_part:
            parts.append((current_part, is_bold))
        
        # Replace the text with formatted version
        cursor.removeSelectedText()
        
        for part_text, is_bold in parts:
            format = QTextCharFormat()
            if is_bold:
                format.setFontWeight(QFont.Weight.Bold)
            cursor.insertText(part_text, format)
        
        self.editing_block = False
    
    def mousePressEvent(self, event):
        """Handle mouse press events to revert to original text when editing."""
        super().mousePressEvent(event)
        
        # Get the block under the cursor
        cursor = self.textCursor()
        block = cursor.block()
        position = block.position()
        
        # If this block has original text, revert to it for editing
        if position in self.original_text:
            self.editing_block = True
            
            # Select the entire block
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
            
            # Replace with original text
            cursor.removeSelectedText()
            cursor.insertText(self.original_text[position])
            
            self.editing_block = False