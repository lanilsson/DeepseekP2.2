"""
Terminal Module - Implements terminal functionality

This module contains the TerminalTab class which provides a UI for
accessing and interacting with the system terminal.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt, QProcess, pyqtSlot, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QPlainTextEdit
)
from PyQt6.QtGui import QFont, QTextCursor, QColor

class TerminalTab(QWidget):
    """A tab for accessing and interacting with the system terminal."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.process = None
        self.setup_ui()
        self.start_process()
    
    def setup_ui(self):
        """Set up the terminal UI."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create terminal output area with modern styling
        self.terminal_output = QPlainTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(QFont("Courier New", 11))
        self.terminal_output.setStyleSheet("""
            background-color: #121212;
            color: #f0f0f0;
            border: none;
            border-radius: 6px;
        """)
        
        # Create command input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        # Command prompt
        self.prompt_label = QLabel("$")
        self.prompt_label.setStyleSheet("color: #64FFDA; font-weight: bold; font-size: 14px;")
        input_layout.addWidget(self.prompt_label)
        
        # Command input
        self.command_input = QLineEdit()
        self.command_input.setStyleSheet("""
            background-color: #1e1e1e;
            color: #f0f0f0;
            border: 1px solid #333333;
            border-radius: 4px;
            padding: 6px;
            font-family: 'Courier New', monospace;
            font-size: 11px;
        """)
        self.command_input.returnPressed.connect(self.execute_command)
        input_layout.addWidget(self.command_input)
        
        # Execute button
        execute_button = QPushButton("Execute")
        execute_button.setStyleSheet("""
            background-color: #1e1e1e;
            color: #64FFDA;
            border: 1px solid #333333;
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
        """)
        execute_button.clicked.connect(self.execute_command)
        input_layout.addWidget(execute_button)
        
        # Add components to main layout
        main_layout.addWidget(self.terminal_output)
        main_layout.addLayout(input_layout)
        
        # Add current directory display with modern styling
        self.dir_label = QLabel(f"📁 {os.getcwd()}")
        self.dir_label.setStyleSheet("""
            color: #64FFDA;
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            padding: 4px;
            background-color: #1e1e1e;
            border-radius: 4px;
        """)
        main_layout.addWidget(self.dir_label)
    
    def display_welcome_message(self):
        """Display a stylish welcome message in the terminal."""
        welcome_text = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                            JORDAN AI TERMINAL                                ║
║                                                                              ║
║                                                                              ║
║        ░░░░░██╗░█████╗░██████╗░██████╗░░█████╗░███╗░░██╗  ░█████╗░██╗        ║
║        ░░░░░██║██╔══██╗██╔══██╗██╔══██╗██╔══██╗████╗░██║  ██╔══██╗██║        ║
║        ░░░░░██║██║░░██║██████╔╝██║░░██║███████║██╔██╗██║  ███████║██║        ║
║        ██╗░░██║██║░░██║██╔══██╗██║░░██║██╔══██║██║╚████║  ██╔══██║██║        ║
║        ╚█████╔╝╚█████╔╝██║░░██║██████╔╝██║░░██║██║░╚███║  ██║░░██║██║        ║
║        ░╚════╝░░╚════╝░╚═╝░░╚═╝╚═════╝░╚═╝░░╚═╝╚═╝░░╚══╝  ╚═╝░░╚═╝╚═╝        ║
║                                                                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        # Set text color to a vibrant teal for the welcome message
        cursor = self.terminal_output.textCursor()
        format = cursor.charFormat()
        format.setForeground(QColor("#00FFFF"))  # Bright cyan
        cursor.setCharFormat(format)
        
        self.terminal_output.appendPlainText(welcome_text)
        
        # Reset text color
        format.setForeground(QColor("#f0f0f0"))
        cursor.setCharFormat(format)
        
        # Add system info with modern styling
        self.terminal_output.appendPlainText("╔═══ SYSTEM INFO " + "═" * 50)
        self.terminal_output.appendPlainText(f"║ OS      : {platform.system()} {platform.release()}")
        self.terminal_output.appendPlainText(f"║ Python  : {platform.python_version()}")
        self.terminal_output.appendPlainText(f"║ Path    : {os.getcwd()}")
        self.terminal_output.appendPlainText("╚" + "═" * 63)
        self.terminal_output.appendPlainText("\nType 'help' for available commands\n")
    
    def start_process(self):
        """Start the terminal process."""
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        
        # Display the welcome message
        self.display_welcome_message()
        
        # Determine the shell to use based on the platform
        if platform.system() == "Windows":
            self.process.start("cmd.exe")
        else:  # Unix-like systems (macOS, Linux)
            # Use /bin/sh (root shell) instead of user's shell
            shell = "/bin/sh"
            self.process.start(shell)
    
    def handle_stdout(self):
        """Handle standard output from the process."""
        try:
            if self.process and self.process.state() == QProcess.ProcessState.Running:
                data = self.process.readAllStandardOutput().data().decode()
                
                # Filter out directory spam (common pattern in shell output)
                if data.strip() == os.getcwd() or '/Users/' in data and '\n' not in data:
                    return
                
                self.terminal_output.appendPlainText(data)
                self.terminal_output.moveCursor(QTextCursor.MoveOperation.End)
        except Exception as e:
            self.terminal_output.appendPlainText(f"Error reading output: {str(e)}")
    
    def handle_stderr(self):
        """Handle standard error from the process."""
        try:
            if self.process and self.process.state() == QProcess.ProcessState.Running:
                data = self.process.readAllStandardError().data().decode()
                
                # Filter out directory spam (common pattern in shell output)
                if data.strip() == os.getcwd() or '/Users/' in data and '\n' not in data:
                    return
                
                # Set text color to red for errors
                cursor = self.terminal_output.textCursor()
                format = cursor.charFormat()
                format.setForeground(QColor("red"))
                cursor.setCharFormat(format)
                
                self.terminal_output.appendPlainText(data)
                
                # Reset text color
                format.setForeground(QColor("#f0f0f0"))
                cursor.setCharFormat(format)
                
                self.terminal_output.moveCursor(QTextCursor.MoveOperation.End)
        except Exception as e:
            self.terminal_output.appendPlainText(f"Error reading error output: {str(e)}")
    
    def execute_command(self):
        """Execute the command entered by the user."""
        command = self.command_input.text().strip()
        if not command:
            return
        
        # Special handling for clear command
        if command == "clear":
            self.terminal_output.clear()
            self.command_input.clear()
            return
        
        # Special handling for exit/quit commands
        if command in ["exit", "quit"]:
            self.terminal_output.appendPlainText("Cannot exit the terminal in this interface.")
            self.command_input.clear()
            return
        
        try:
            if self.process and self.process.state() == QProcess.ProcessState.Running:
                # Display the command in the terminal output
                self.terminal_output.appendPlainText(f"$ {command}")
                
                # Write the command to the process
                self.process.write(f"{command}\n".encode())
                
                # Clear the command input
                self.command_input.clear()
            else:
                self.terminal_output.appendPlainText("Terminal process is not running. Restarting...")
                self.start_process()
                # Try again after restarting
                QTimer.singleShot(500, lambda: self.process.write(f"{command}\n".encode()))
        except Exception as e:
            self.terminal_output.appendPlainText(f"Error executing command: {str(e)}")
            self.command_input.clear()
    
    def update_current_directory(self):
        """Update the current directory display."""
        # Don't automatically run pwd/cd commands after each command
        # This was causing the terminal to spam the current directory
        pass
    
    def process_finished(self, exit_code, exit_status):
        """Handle process termination."""
        self.terminal_output.appendPlainText(f"\nProcess terminated with exit code: {exit_code}")
        
        # Restart the process if it terminated
        self.start_process()
    
    def closeEvent(self, event):
        """Handle tab close event."""
        try:
            if self.process and self.process.state() == QProcess.ProcessState.Running:
                self.process.terminate()
                self.process.waitForFinished(1000)
                if self.process.state() == QProcess.ProcessState.Running:
                    self.process.kill()
        except Exception as e:
            print(f"Error closing terminal process: {str(e)}")