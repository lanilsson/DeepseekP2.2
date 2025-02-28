"""
AI Browser Tab - UI component for interacting with the AI middleware

This module provides a tab interface for controlling the AI middleware
that connects the r1-1776 model to the browser controller.
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QTabWidget, QSlider, QProgressBar, QGroupBox,
    QCheckBox, QSpinBox, QDoubleSpinBox, QFrame, QSplitter,
    QScrollArea, QSizePolicy, QTextEdit, QLineEdit, QFileDialog,
    QRadioButton, QButtonGroup
)
from PyQt6.QtGui import QFont, QColor, QTextCursor

from selenium_qt_browser.tab_types import TabType
# Use lazy imports for middleware to avoid circular imports
# from selenium_qt_browser.ai_browser_middleware import AIBrowserMiddleware, get_middleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class LogHandler(logging.Handler):
    """Custom log handler that emits log records to a signal."""
    
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
    
    def emit(self, record):
        log_entry = self.format(record)
        self.signal.emit(log_entry)

class AIBrowserTab(QWidget):
    """Tab for controlling the AI middleware."""
    
    log_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.tab_type = TabType.AI_BROWSER
        
        # Lazy import middleware to avoid circular imports
        from selenium_qt_browser.ai_browser_middleware import get_middleware
        self.middleware = get_middleware()
        
        # Set up the UI
        self.init_ui()
        
        # Set up logging
        self.setup_logging()
        
        # Update timer for status
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Update every second
    
    def init_ui(self):
        """Initialize the UI."""
        main_layout = QVBoxLayout(self)
        
        # Header with title
        header_layout = QHBoxLayout()
        title_label = QLabel("R1-1776 AI Browser Control")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("Status: Not Running")
        header_layout.addWidget(self.status_label)
        
        main_layout.addLayout(header_layout)
        
        # Create a splitter for the main content
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top section: Controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        
        # Model configuration
        model_group = QGroupBox("Model Configuration")
        model_layout = QVBoxLayout(model_group)
        
        # Model path
        model_path_layout = QHBoxLayout()
        model_path_layout.addWidget(QLabel("Model Path:"))
        self.model_path_edit = QLineEdit()
        self.model_path_edit.setText(os.path.join(os.path.expanduser("~"), ".cache", "r1-1776"))
        model_path_layout.addWidget(self.model_path_edit)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_model_path)
        model_path_layout.addWidget(browse_button)
        
        model_layout.addLayout(model_path_layout)
        
        # Precision options
        precision_layout = QHBoxLayout()
        precision_layout.addWidget(QLabel("Precision:"))
        
        self.precision_group = QButtonGroup(self)
        
        self.fp16_radio = QRadioButton("FP16")
        self.fp16_radio.setChecked(True)
        self.precision_group.addButton(self.fp16_radio)
        precision_layout.addWidget(self.fp16_radio)
        
        self.int8_radio = QRadioButton("8-bit")
        self.precision_group.addButton(self.int8_radio)
        precision_layout.addWidget(self.int8_radio)
        
        self.int4_radio = QRadioButton("4-bit")
        self.precision_group.addButton(self.int4_radio)
        precision_layout.addWidget(self.int4_radio)
        
        model_layout.addLayout(precision_layout)
        
        # Device options
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Device:"))
        
        self.device_group = QButtonGroup(self)
        
        self.auto_radio = QRadioButton("Auto")
        self.auto_radio.setChecked(True)
        self.device_group.addButton(self.auto_radio)
        device_layout.addWidget(self.auto_radio)
        
        self.cpu_radio = QRadioButton("CPU")
        self.device_group.addButton(self.cpu_radio)
        device_layout.addWidget(self.cpu_radio)
        
        model_layout.addLayout(device_layout)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        
        self.load_model_button = QPushButton("Load Model")
        self.load_model_button.clicked.connect(self.load_model)
        buttons_layout.addWidget(self.load_model_button)
        
        self.unload_model_button = QPushButton("Unload Model")
        self.unload_model_button.clicked.connect(self.unload_model)
        self.unload_model_button.setEnabled(False)
        buttons_layout.addWidget(self.unload_model_button)
        
        model_layout.addLayout(buttons_layout)
        
        controls_layout.addWidget(model_group)
        
        # AI control
        ai_group = QGroupBox("AI Control")
        ai_layout = QVBoxLayout(ai_group)
        
        # AI settings
        settings_layout = QHBoxLayout()
        
        settings_layout.addWidget(QLabel("Temperature:"))
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.1, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.7)
        settings_layout.addWidget(self.temperature_spin)
        
        settings_layout.addWidget(QLabel("Top P:"))
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.1, 1.0)
        self.top_p_spin.setSingleStep(0.05)
        self.top_p_spin.setValue(0.95)
        settings_layout.addWidget(self.top_p_spin)
        
        ai_layout.addLayout(settings_layout)
        
        # AI control buttons
        ai_buttons_layout = QHBoxLayout()
        
        self.start_ai_button = QPushButton("Start AI")
        self.start_ai_button.clicked.connect(self.start_ai)
        self.start_ai_button.setEnabled(False)
        ai_buttons_layout.addWidget(self.start_ai_button)
        
        self.stop_ai_button = QPushButton("Stop AI")
        self.stop_ai_button.clicked.connect(self.stop_ai)
        self.stop_ai_button.setEnabled(False)
        ai_buttons_layout.addWidget(self.stop_ai_button)
        
        ai_layout.addLayout(ai_buttons_layout)
        
        controls_layout.addWidget(ai_group)
        
        # Manual control
        manual_group = QGroupBox("Manual Control")
        manual_layout = QVBoxLayout(manual_group)
        
        # Action input
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("Action:"))
        
        self.action_combo = QComboBox()
        self.action_combo.addItems(["navigate", "click", "fill", "back", "forward", "refresh"])
        action_layout.addWidget(self.action_combo)
        
        manual_layout.addLayout(action_layout)
        
        # Parameters input
        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel("Parameters:"))
        
        self.params_edit = QLineEdit()
        self.params_edit.setPlaceholderText('{"url": "https://example.com"} or {"selector": "#search-button"}')
        params_layout.addWidget(self.params_edit)
        
        manual_layout.addLayout(params_layout)
        
        # Execute button
        execute_layout = QHBoxLayout()
        
        self.execute_button = QPushButton("Execute Action")
        self.execute_button.clicked.connect(self.execute_manual_action)
        self.execute_button.setEnabled(False)
        execute_layout.addWidget(self.execute_button)
        
        manual_layout.addLayout(execute_layout)
        
        controls_layout.addWidget(manual_group)
        
        splitter.addWidget(controls_widget)
        
        # Bottom section: Log output
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        log_label = QLabel("AI Activity Log:")
        log_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.log_text.setStyleSheet("font-family: monospace;")
        log_layout.addWidget(self.log_text)
        
        # Clear log button
        clear_log_button = QPushButton("Clear Log")
        clear_log_button.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_button)
        
        splitter.addWidget(log_widget)
        
        # Set initial sizes for the splitter
        splitter.setSizes([300, 400])
        
        main_layout.addWidget(splitter)
    
    def setup_logging(self):
        """Set up logging to the log text widget."""
        # Create a custom handler that emits to our signal
        handler = LogHandler(self.log_signal)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        handler.setLevel(logging.INFO)
        
        # Add the handler to the logger
        # Use string name to avoid import
        logger = logging.getLogger("selenium_qt_browser.ai_browser_middleware")
        logger.addHandler(handler)
        
        # Connect the signal to our slot
        self.log_signal.connect(self.append_log)
    
    def append_log(self, text):
        """Append text to the log widget."""
        self.log_text.append(text)
        # Scroll to the bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def clear_log(self):
        """Clear the log widget."""
        self.log_text.clear()
    
    def browse_model_path(self):
        """Open a file dialog to browse for the model path."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Model Directory",
            self.model_path_edit.text()
        )
        if directory:
            self.model_path_edit.setText(directory)
    
    def load_model(self):
        """Load the model with the specified configuration."""
        try:
            # Get the model path
            model_path = self.model_path_edit.text()
            
            # Create configuration based on selected options
            force_config = {}
            
            # Precision
            if self.int8_radio.isChecked():
                force_config["load_in_8bit"] = True
            elif self.int4_radio.isChecked():
                force_config["load_in_4bit"] = True
                force_config["bnb_4bit_compute_dtype"] = torch.float16
                force_config["bnb_4bit_quant_type"] = "nf4"
            
            # Device
            if self.cpu_radio.isChecked():
                force_config["device_map"] = "cpu"
            
            # Update the middleware model path
            self.middleware.model_path = model_path
            
            # Load the model
            self.append_log(f"Loading model from {model_path}...")
            self.middleware.load_model(force_config)
            
            # Update UI
            self.load_model_button.setEnabled(False)
            self.unload_model_button.setEnabled(True)
            self.start_ai_button.setEnabled(True)
            self.execute_button.setEnabled(True)
            
            self.append_log("Model loaded successfully")
            
        except Exception as e:
            self.append_log(f"Error loading model: {e}")
    
    def unload_model(self):
        """Unload the model."""
        try:
            # Stop the AI if it's running
            if self.middleware.running:
                self.stop_ai()
            
            # Unload the model
            self.append_log("Unloading model...")
            self.middleware.unload_model()
            
            # Update UI
            self.load_model_button.setEnabled(True)
            self.unload_model_button.setEnabled(False)
            self.start_ai_button.setEnabled(False)
            self.stop_ai_button.setEnabled(False)
            self.execute_button.setEnabled(False)
            
            self.append_log("Model unloaded successfully")
            
        except Exception as e:
            self.append_log(f"Error unloading model: {e}")
    
    def start_ai(self):
        """Start the AI processing loop."""
        try:
            # Start the AI
            self.append_log("Starting AI processing loop...")
            self.middleware.start()
            
            # Update UI
            self.start_ai_button.setEnabled(False)
            self.stop_ai_button.setEnabled(True)
            
            self.append_log("AI processing loop started")
            
        except Exception as e:
            self.append_log(f"Error starting AI: {e}")
    
    def stop_ai(self):
        """Stop the AI processing loop."""
        try:
            # Stop the AI
            self.append_log("Stopping AI processing loop...")
            self.middleware.stop()
            
            # Update UI
            self.start_ai_button.setEnabled(True)
            self.stop_ai_button.setEnabled(False)
            
            self.append_log("AI processing loop stopped")
            
        except Exception as e:
            self.append_log(f"Error stopping AI: {e}")
    
    def execute_manual_action(self):
        """Execute a manual action."""
        try:
            # Get the action type
            action_type = self.action_combo.currentText()
            
            # Get the parameters
            params_text = self.params_edit.text()
            if not params_text:
                params = {}
            else:
                try:
                    params = json.loads(params_text)
                except json.JSONDecodeError:
                    self.append_log("Error: Invalid JSON parameters")
                    return
            
            # Create the action
            action = {"action": action_type, **params}
            
            # Execute the action
            self.append_log(f"Executing manual action: {action}")
            self.middleware._execute_action(action)
            
        except Exception as e:
            self.append_log(f"Error executing action: {e}")
    
    def update_status(self):
        """Update the status label."""
        if not hasattr(self, 'middleware'):
            return
        
        # Update model status
        if self.middleware.model_loaded:
            model_status = "Loaded"
        else:
            model_status = "Not Loaded"
        
        # Update AI status
        if self.middleware.running:
            ai_status = "Running"
        else:
            ai_status = "Stopped"
        
        # Update the status label
        self.status_label.setText(f"Status: Model: {model_status}, AI: {ai_status}")