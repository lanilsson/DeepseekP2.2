#!/usr/bin/env python3
"""
Resource Monitor for R1-1776 Model

This module provides functionality to monitor and manage GPU/CPU resources
while running the r1-1776 model alongside the Jordan AI browser application.
It includes real-time graphing and resource management controls.
"""

import os
import sys
import time
import threading
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union

import psutil
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    HAS_GPUTIL = False

try:
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QComboBox, QTabWidget, QSlider, QProgressBar, QGroupBox,
        QCheckBox, QSpinBox, QDoubleSpinBox, QFrame, QSplitter,
        QScrollArea, QSizePolicy
    )
    from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QLinearGradient, QGradient
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False

# Configure logging
logger = logging.getLogger(__name__)

# Constants
UPDATE_INTERVAL_MS = 1000  # Update interval in milliseconds
HISTORY_LENGTH = 60  # Number of data points to keep in history (60 seconds)
COLORS = {
    "cpu": "#4e79a7",
    "ram": "#f28e2c",
    "gpu": "#e15759",
    "vram": "#76b7b2",
    "background": "#f9f9f9",
    "grid": "#dddddd",
    "text": "#333333",
    "warning": "#e15759",
    "good": "#59a14f"
}

class ResourceData:
    """Class to store and manage resource usage data."""
    
    def __init__(self, history_length: int = HISTORY_LENGTH):
        self.history_length = history_length
        self.reset()
    
    def reset(self):
        """Reset all data."""
        self.timestamps: List[datetime] = []
        self.cpu_usage: List[float] = []
        self.ram_usage: List[float] = []
        self.ram_total: float = 0
        self.gpu_usage: List[List[float]] = []  # List of lists for multiple GPUs
        self.gpu_memory: List[List[float]] = []  # List of lists for multiple GPUs
        self.gpu_total_memory: List[float] = []  # Total memory for each GPU
        self.gpu_names: List[str] = []
        self.gpu_temperatures: List[List[float]] = []  # List of lists for multiple GPUs
        self.model_memory: List[float] = []  # Memory used by the model
        self.model_loaded = False
        self.model_device = "N/A"
        self.model_precision = "N/A"
        self.model_name = "N/A"
    
    def update(self):
        """Update resource usage data."""
        now = datetime.now()
        
        # Add new timestamp
        self.timestamps.append(now)
        if len(self.timestamps) > self.history_length:
            self.timestamps.pop(0)
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=None)
        self.cpu_usage.append(cpu_percent)
        if len(self.cpu_usage) > self.history_length:
            self.cpu_usage.pop(0)
        
        # RAM usage
        memory = psutil.virtual_memory()
        self.ram_total = memory.total / (1024 ** 3)  # GB
        ram_used = memory.used / (1024 ** 3)  # GB
        self.ram_usage.append(ram_used)
        if len(self.ram_usage) > self.history_length:
            self.ram_usage.pop(0)
        
        # GPU usage (if available)
        if HAS_GPUTIL:
            try:
                gpus = GPUtil.getGPUs()
                
                # Initialize lists if this is the first update
                if not self.gpu_names:
                    self.gpu_names = [gpu.name for gpu in gpus]
                    self.gpu_total_memory = [gpu.memoryTotal / 1024 for gpu in gpus]  # GB
                    self.gpu_usage = [[] for _ in gpus]
                    self.gpu_memory = [[] for _ in gpus]
                    self.gpu_temperatures = [[] for _ in gpus]
                
                # Update GPU data
                for i, gpu in enumerate(gpus):
                    self.gpu_usage[i].append(gpu.load * 100)  # Convert to percentage
                    self.gpu_memory[i].append(gpu.memoryUsed / 1024)  # GB
                    self.gpu_temperatures[i].append(gpu.temperature)
                    
                    # Trim lists if they exceed history length
                    if len(self.gpu_usage[i]) > self.history_length:
                        self.gpu_usage[i].pop(0)
                    if len(self.gpu_memory[i]) > self.history_length:
                        self.gpu_memory[i].pop(0)
                    if len(self.gpu_temperatures[i]) > self.history_length:
                        self.gpu_temperatures[i].pop(0)
            except Exception as e:
                logger.warning(f"Error updating GPU data: {e}")
        
        # PyTorch GPU usage (more accurate for model memory)
        if HAS_TORCH and torch.cuda.is_available():
            try:
                # Update model memory usage if model is loaded
                if self.model_loaded:
                    model_memory = 0
                    for i in range(torch.cuda.device_count()):
                        model_memory += torch.cuda.memory_allocated(i) / (1024 ** 3)  # GB
                    self.model_memory.append(model_memory)
                    if len(self.model_memory) > self.history_length:
                        self.model_memory.pop(0)
            except Exception as e:
                logger.warning(f"Error updating PyTorch GPU data: {e}")
    
    def set_model_info(self, loaded: bool, device: str, precision: str, name: str):
        """Set information about the loaded model."""
        self.model_loaded = loaded
        self.model_device = device
        self.model_precision = precision
        self.model_name = name
    
    def get_latest(self) -> Dict[str, Any]:
        """Get the latest resource usage data."""
        result = {
            "timestamp": self.timestamps[-1] if self.timestamps else datetime.now(),
            "cpu_usage": self.cpu_usage[-1] if self.cpu_usage else 0,
            "ram_usage": self.ram_usage[-1] if self.ram_usage else 0,
            "ram_total": self.ram_total,
            "gpu_count": len(self.gpu_names),
            "gpu_names": self.gpu_names,
            "gpu_usage": [usage[-1] if usage else 0 for usage in self.gpu_usage],
            "gpu_memory": [memory[-1] if memory else 0 for memory in self.gpu_memory],
            "gpu_total_memory": self.gpu_total_memory,
            "gpu_temperatures": [temp[-1] if temp else 0 for temp in self.gpu_temperatures],
            "model_memory": self.model_memory[-1] if self.model_memory else 0,
            "model_loaded": self.model_loaded,
            "model_device": self.model_device,
            "model_precision": self.model_precision,
            "model_name": self.model_name
        }
        return result
    
    def get_history(self) -> Dict[str, Any]:
        """Get the full history of resource usage data."""
        result = {
            "timestamps": self.timestamps,
            "cpu_usage": self.cpu_usage,
            "ram_usage": self.ram_usage,
            "ram_total": self.ram_total,
            "gpu_count": len(self.gpu_names),
            "gpu_names": self.gpu_names,
            "gpu_usage": self.gpu_usage,
            "gpu_memory": self.gpu_memory,
            "gpu_total_memory": self.gpu_total_memory,
            "gpu_temperatures": self.gpu_temperatures,
            "model_memory": self.model_memory,
            "model_loaded": self.model_loaded,
            "model_device": self.model_device,
            "model_precision": self.model_precision,
            "model_name": self.model_name
        }
        return result


class ResourceMonitor(QObject):
    """Class to monitor system resources."""
    
    data_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = ResourceData()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.running = False
    
    def start(self, interval_ms: int = UPDATE_INTERVAL_MS):
        """Start monitoring resources."""
        if not self.running:
            self.timer.start(interval_ms)
            self.running = True
    
    def stop(self):
        """Stop monitoring resources."""
        if self.running:
            self.timer.stop()
            self.running = False
    
    def update_data(self):
        """Update resource usage data and emit signal."""
        self.data.update()
        self.data_updated.emit(self.data.get_latest())
    
    def set_model_info(self, loaded: bool, device: str, precision: str, name: str):
        """Set information about the loaded model."""
        self.data.set_model_info(loaded, device, precision, name)
    
    def get_latest(self) -> Dict[str, Any]:
        """Get the latest resource usage data."""
        return self.data.get_latest()
    
    def get_history(self) -> Dict[str, Any]:
        """Get the full history of resource usage data."""
        return self.data.get_history()


class LineGraphWidget(QWidget):
    """Widget for displaying line graphs of resource usage."""
    
    def __init__(self, title: str, color: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        self.data = []
        self.max_value = 100
        self.min_value = 0
        self.setMinimumHeight(150)
        self.setMinimumWidth(300)
    
    def set_data(self, data: List[float], max_value: Optional[float] = None):
        """Set data for the graph."""
        self.data = data
        if max_value is not None:
            self.max_value = max_value
        self.update()
    
    def paintEvent(self, event):
        """Paint the graph."""
        if not self.data:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(COLORS["background"]))
        
        # Draw title
        painter.setPen(QColor(COLORS["text"]))
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(10, 20, self.title)
        
        # Draw grid
        painter.setPen(QPen(QColor(COLORS["grid"]), 1, Qt.PenStyle.DotLine))
        width = self.width()
        height = self.height()
        margin = 30  # Margin for labels
        
        # Horizontal grid lines (25%, 50%, 75%, 100%)
        for i in range(1, 5):
            y = height - margin - (height - 2 * margin) * (i * 0.25)
            painter.drawLine(margin, int(y), width - margin, int(y))
            painter.setPen(QColor(COLORS["text"]))
            painter.drawText(5, int(y) + 5, f"{int(self.max_value * i * 0.25)}")
            painter.setPen(QPen(QColor(COLORS["grid"]), 1, Qt.PenStyle.DotLine))
        
        # Draw data line
        if len(self.data) > 1:
            painter.setPen(QPen(QColor(self.color), 2))
            
            path_points = []
            for i, value in enumerate(self.data):
                x = margin + (width - 2 * margin) * i / (len(self.data) - 1)
                y = height - margin - (height - 2 * margin) * (value - self.min_value) / (self.max_value - self.min_value)
                path_points.append((x, y))
            
            for i in range(len(path_points) - 1):
                painter.drawLine(
                    int(path_points[i][0]), int(path_points[i][1]),
                    int(path_points[i+1][0]), int(path_points[i+1][1])
                )
            
            # Draw latest value
            latest_value = self.data[-1]
            painter.setPen(QColor(COLORS["text"]))
            painter.drawText(width - 70, 20, f"{latest_value:.1f}")
        
        painter.end()


class MultiLineGraphWidget(QWidget):
    """Widget for displaying multiple line graphs on the same chart."""
    
    def __init__(self, title: str, labels: List[str], colors: List[str], parent=None):
        super().__init__(parent)
        self.title = title
        self.labels = labels
        self.colors = colors
        self.data_series = [[] for _ in labels]
        self.max_value = 100
        self.min_value = 0
        self.setMinimumHeight(200)
        self.setMinimumWidth(300)
    
    def set_data(self, data_series: List[List[float]], max_value: Optional[float] = None):
        """Set data for the graph."""
        self.data_series = data_series
        if max_value is not None:
            self.max_value = max_value
        self.update()
    
    def paintEvent(self, event):
        """Paint the graph."""
        if not self.data_series or not all(self.data_series):
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(COLORS["background"]))
        
        # Draw title
        painter.setPen(QColor(COLORS["text"]))
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(10, 20, self.title)
        
        # Draw grid
        painter.setPen(QPen(QColor(COLORS["grid"]), 1, Qt.PenStyle.DotLine))
        width = self.width()
        height = self.height()
        margin = 30  # Margin for labels
        legend_height = 20 * len(self.labels)  # Height for the legend
        
        # Horizontal grid lines (25%, 50%, 75%, 100%)
        for i in range(1, 5):
            y = height - margin - legend_height - (height - 2 * margin - legend_height) * (i * 0.25)
            painter.drawLine(margin, int(y), width - margin, int(y))
            painter.setPen(QColor(COLORS["text"]))
            painter.drawText(5, int(y) + 5, f"{int(self.max_value * i * 0.25)}")
            painter.setPen(QPen(QColor(COLORS["grid"]), 1, Qt.PenStyle.DotLine))
        
        # Draw data lines
        for series_idx, data in enumerate(self.data_series):
            if len(data) > 1:
                painter.setPen(QPen(QColor(self.colors[series_idx]), 2))
                
                path_points = []
                for i, value in enumerate(data):
                    x = margin + (width - 2 * margin) * i / (len(data) - 1)
                    y = height - margin - legend_height - (height - 2 * margin - legend_height) * (value - self.min_value) / (self.max_value - self.min_value)
                    path_points.append((x, y))
                
                for i in range(len(path_points) - 1):
                    painter.drawLine(
                        int(path_points[i][0]), int(path_points[i][1]),
                        int(path_points[i+1][0]), int(path_points[i+1][1])
                    )
        
        # Draw legend
        for i, label in enumerate(self.labels):
            y = height - legend_height + i * 20
            painter.setPen(QColor(self.colors[i]))
            painter.drawLine(margin, y, margin + 20, y)
            painter.setPen(QColor(COLORS["text"]))
            painter.drawText(margin + 30, y + 5, f"{label}: {self.data_series[i][-1]:.1f}")
        
        painter.end()


class GaugeWidget(QWidget):
    """Widget for displaying a gauge with a single value."""
    
    def __init__(self, title: str, color: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        self.value = 0
        self.max_value = 100
        self.setMinimumHeight(120)
        self.setMinimumWidth(120)
    
    def set_value(self, value: float, max_value: Optional[float] = None):
        """Set the value for the gauge."""
        self.value = value
        if max_value is not None:
            self.max_value = max_value
        self.update()
    
    def paintEvent(self, event):
        """Paint the gauge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(COLORS["background"]))
        
        # Draw title
        painter.setPen(QColor(COLORS["text"]))
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(10, 20, self.title)
        
        # Draw gauge
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2 + 10
        radius = min(width, height) / 2 - 20
        
        # Draw background arc
        painter.setPen(QPen(QColor(COLORS["grid"]), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2), 225 * 16, 90 * 16)
        
        # Draw value arc
        percentage = min(1.0, self.value / self.max_value)
        painter.setPen(QPen(QColor(self.color), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2), 225 * 16, int(-percentage * 90 * 16))
        
        # Draw value text
        painter.setPen(QColor(COLORS["text"]))
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)
        text = f"{self.value:.1f}"
        text_rect = painter.fontMetrics().boundingRect(text)
        painter.drawText(int(center_x - text_rect.width() / 2), int(center_y + 5), text)
        
        painter.end()


class ResourceMonitorWidget(QWidget):
    """Widget for displaying resource usage."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor = ResourceMonitor(self)
        self.monitor.data_updated.connect(self.update_ui)
        self.init_ui()
        self.monitor.start()
    
    def init_ui(self):
        """Initialize the UI."""
        main_layout = QVBoxLayout(self)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        title_label = QLabel("R1-1776 Resource Monitor")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.refresh_rate_combo = QComboBox()
        self.refresh_rate_combo.addItems(["1s", "2s", "5s"])
        self.refresh_rate_combo.setCurrentIndex(0)
        self.refresh_rate_combo.currentIndexChanged.connect(self.change_refresh_rate)
        header_layout.addWidget(QLabel("Refresh:"))
        header_layout.addWidget(self.refresh_rate_combo)
        
        main_layout.addLayout(header_layout)
        
        # Tabs for different views
        self.tabs = QTabWidget()
        
        # Overview tab
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        
        # System info section
        system_group = QGroupBox("System Information")
        system_layout = QHBoxLayout(system_group)
        
        # CPU and RAM gauges
        cpu_gauge = GaugeWidget("CPU", COLORS["cpu"])
        ram_gauge = GaugeWidget("RAM", COLORS["ram"])
        self.cpu_gauge = cpu_gauge
        self.ram_gauge = ram_gauge
        
        system_layout.addWidget(cpu_gauge)
        system_layout.addWidget(ram_gauge)
        
        # GPU gauges (will be added dynamically if GPUs are detected)
        self.gpu_gauges = []
        self.gpu_layout = system_layout
        
        overview_layout.addWidget(system_group)
        
        # Graphs section
        graphs_group = QGroupBox("Resource Usage History")
        graphs_layout = QVBoxLayout(graphs_group)
        
        # CPU and RAM graphs
        self.cpu_graph = LineGraphWidget("CPU Usage (%)", COLORS["cpu"])
        self.ram_graph = LineGraphWidget("RAM Usage (GB)", COLORS["ram"])
        
        graphs_layout.addWidget(self.cpu_graph)
        graphs_layout.addWidget(self.ram_graph)
        
        # GPU graphs (will be added dynamically if GPUs are detected)
        self.gpu_usage_graphs = []
        self.gpu_memory_graphs = []
        self.gpu_graphs_layout = graphs_layout
        
        overview_layout.addWidget(graphs_group)
        
        # Model info section
        model_group = QGroupBox("Model Information")
        model_layout = QVBoxLayout(model_group)
        
        model_info_layout = QHBoxLayout()
        self.model_name_label = QLabel("Model: Not loaded")
        self.model_device_label = QLabel("Device: N/A")
        self.model_precision_label = QLabel("Precision: N/A")
        model_info_layout.addWidget(self.model_name_label)
        model_info_layout.addWidget(self.model_device_label)
        model_info_layout.addWidget(self.model_precision_label)
        
        model_layout.addLayout(model_info_layout)
        
        # Model memory graph
        self.model_memory_graph = LineGraphWidget("Model Memory Usage (GB)", COLORS["vram"])
        model_layout.addWidget(self.model_memory_graph)
        
        overview_layout.addWidget(model_group)
        
        # Add overview tab
        self.tabs.addTab(overview_tab, "Overview")
        
        # GPU Details tab (will be added if GPUs are detected)
        self.gpu_tab = QWidget()
        self.gpu_tab_layout = QVBoxLayout(self.gpu_tab)
        
        # Add tabs to main layout
        main_layout.addWidget(self.tabs)
        
        # Controls section
        controls_group = QGroupBox("Resource Management")
        controls_layout = QHBoxLayout(controls_group)
        
        # Model loading controls
        model_controls_layout = QVBoxLayout()
        model_controls_layout.addWidget(QLabel("Model Configuration:"))
        
        precision_layout = QHBoxLayout()
        precision_layout.addWidget(QLabel("Precision:"))
        self.precision_combo = QComboBox()
        self.precision_combo.addItems(["FP16", "8-bit", "4-bit"])
        precision_layout.addWidget(self.precision_combo)
        model_controls_layout.addLayout(precision_layout)
        
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Device:"))
        self.device_combo = QComboBox()
        self.device_combo.addItems(["Auto", "CPU"])
        device_layout.addWidget(self.device_combo)
        model_controls_layout.addLayout(device_layout)
        
        load_button = QPushButton("Load Model")
        load_button.clicked.connect(self.load_model)
        unload_button = QPushButton("Unload Model")
        unload_button.clicked.connect(self.unload_model)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(load_button)
        buttons_layout.addWidget(unload_button)
        model_controls_layout.addLayout(buttons_layout)
        
        controls_layout.addLayout(model_controls_layout)
        
        # Memory management controls
        memory_controls_layout = QVBoxLayout()
        memory_controls_layout.addWidget(QLabel("Memory Management:"))
        
        cache_layout = QHBoxLayout()
        self.clear_cache_button = QPushButton("Clear Cache")
        self.clear_cache_button.clicked.connect(self.clear_cache)
        cache_layout.addWidget(self.clear_cache_button)
        memory_controls_layout.addLayout(cache_layout)
        
        gc_layout = QHBoxLayout()
        self.run_gc_button = QPushButton("Run Garbage Collection")
        self.run_gc_button.clicked.connect(self.run_garbage_collection)
        gc_layout.addWidget(self.run_gc_button)
        memory_controls_layout.addLayout(gc_layout)
        
        controls_layout.addLayout(memory_controls_layout)
        
        main_layout.addWidget(controls_group)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Monitoring resources...")
        status_layout.addWidget(self.status_label)
        
        main_layout.addLayout(status_layout)
    
    def update_ui(self, data: Dict[str, Any]):
        """Update the UI with new resource data."""
        # Update CPU and RAM gauges
        self.cpu_gauge.set_value(data["cpu_usage"])
        self.ram_gauge.set_value(data["ram_usage"], data["ram_total"])
        
        # Update CPU and RAM graphs
        history = self.monitor.get_history()
        self.cpu_graph.set_data(history["cpu_usage"])
        self.ram_graph.set_data(history["ram_usage"], history["ram_total"])
        
        # Update model info
        if data["model_loaded"]:
            self.model_name_label.setText(f"Model: {data['model_name']}")
            self.model_device_label.setText(f"Device: {data['model_device']}")
            self.model_precision_label.setText(f"Precision: {data['model_precision']}")
            
            # Update model memory graph
            self.model_memory_graph.set_data(history["model_memory"])
        
        # Update GPU information if available
        if data["gpu_count"] > 0:
            # Add GPU tab if not already added
            if self.tabs.count() == 1:
                self.tabs.addTab(self.gpu_tab, "GPU Details")
            
            # Add GPU gauges if not already added
            while len(self.gpu_gauges) < data["gpu_count"]:
                idx = len(self.gpu_gauges)
                gpu_gauge = GaugeWidget(f"GPU {idx}", COLORS["gpu"])
                self.gpu_gauges.append(gpu_gauge)
                self.gpu_layout.addWidget(gpu_gauge)
            
            # Update GPU gauges
            for i, gauge in enumerate(self.gpu_gauges):
                if i < data["gpu_count"]:
                    gauge.set_value(data["gpu_usage"][i], 100)
            
            # Add GPU graphs if not already added
            while len(self.gpu_usage_graphs) < data["gpu_count"]:
                idx = len(self.gpu_usage_graphs)
                gpu_usage_graph = LineGraphWidget(f"GPU {idx} Usage (%)", COLORS["gpu"])
                self.gpu_usage_graphs.append(gpu_usage_graph)
                self.gpu_graphs_layout.addWidget(gpu_usage_graph)
                
                gpu_memory_graph = LineGraphWidget(f"GPU {idx} Memory (GB)", COLORS["vram"])
                self.gpu_memory_graphs.append(gpu_memory_graph)
                self.gpu_graphs_layout.addWidget(gpu_memory_graph)
            
            # Update GPU graphs
            for i, graph in enumerate(self.gpu_usage_graphs):
                if i < data["gpu_count"]:
                    graph.set_data(history["gpu_usage"][i])
            
            for i, graph in enumerate(self.gpu_memory_graphs):
                if i < data["gpu_count"]:
                    graph.set_data(history["gpu_memory"][i], history["gpu_total_memory"][i])
            
            # Update GPU tab
            if not self.gpu_tab_layout.count():
                for i in range(data["gpu_count"]):
                    gpu_group = QGroupBox(f"GPU {i}: {data['gpu_names'][i]}")
                    gpu_layout = QVBoxLayout(gpu_group)
                    
                    # GPU details
                    details_layout = QHBoxLayout()
                    usage_label = QLabel(f"Usage: {data['gpu_usage'][i]:.1f}%")
                    memory_label = QLabel(f"Memory: {data['gpu_memory'][i]:.1f} GB / {data['gpu_total_memory'][i]:.1f} GB")
                    temp_label = QLabel(f"Temperature: {data['gpu_temperatures'][i]:.1f}°C")
                    details_layout.addWidget(usage_label)
                    details_layout.addWidget(memory_label)
                    details_layout.addWidget(temp_label)
                    
                    gpu_layout.addLayout(details_layout)
                    
                    # GPU graphs
                    gpu_usage_graph = LineGraphWidget(f"GPU {i} Usage (%)", COLORS["gpu"])
                    gpu_usage_graph.set_data(history["gpu_usage"][i])
                    gpu_layout.addWidget(gpu_usage_graph)
                    
                    gpu_memory_graph = LineGraphWidget(f"GPU {i} Memory (GB)", COLORS["vram"])
                    gpu_memory_graph.set_data(history["gpu_memory"][i], history["gpu_total_memory"][i])
                    gpu_layout.addWidget(gpu_memory_graph)
                    
                    self.gpu_tab_layout.addWidget(gpu_group)
    
    def change_refresh_rate(self, index):
        """Change the refresh rate of the monitor."""
        rates = [1000, 2000, 5000]  # milliseconds
        self.monitor.stop()
        self.monitor.start(rates[index])
        self.status_label.setText(f"Refresh rate set to {self.refresh_rate_combo.currentText()}")
    
    def load_model(self):
        """Load the R1-1776 model."""
        try:
            # Get selected configuration
            precision = self.precision_combo.currentText()
            device = self.device_combo.currentText()
            
            # Import the model loading function
            from r1_1776_utils import load_model
            
            # Create configuration based on selected options
            force_config = {}
            if precision == "8-bit":
                force_config["load_in_8bit"] = True
            elif precision == "4-bit":
                force_config["load_in_4bit"] = True
                force_config["bnb_4bit_compute_dtype"] = torch.float16
                force_config["bnb_4bit_quant_type"] = "nf4"
            
            if device == "CPU":
                force_config["device_map"] = "cpu"
            
            # Update status
            self.status_label.setText("Loading model... This may take a while.")
            
            # Load the model in a separate thread to avoid freezing the UI
            threading.Thread(target=self._load_model_thread, args=(force_config,), daemon=True).start()
            
        except ImportError:
            self.status_label.setText("Error: r1_1776_utils module not found.")
        except Exception as e:
            self.status_label.setText(f"Error loading model: {e}")
    
    def _load_model_thread(self, force_config):
        """Thread function to load the model."""
        try:
            from r1_1776_utils import load_model
            
            # Load the model
            tokenizer, model = load_model(force_config=force_config)
            
            # Update model info
            device = "CPU" if force_config.get("device_map") == "cpu" else "GPU"
            precision = "4-bit" if force_config.get("load_in_4bit") else "8-bit" if force_config.get("load_in_8bit") else "FP16"
            
            # Update monitor with model info
            self.monitor.set_model_info(True, device, precision, "R1-1776")
            
            # Update status
            self.status_label.setText(f"Model loaded successfully using {device} with {precision} precision.")
            
        except Exception as e:
            self.status_label.setText(f"Error loading model: {e}")
    
    def unload_model(self):
        """Unload the R1-1776 model."""
        try:
            # Import torch for garbage collection
            import torch
            
            # Clear CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Run garbage collection
            import gc
            gc.collect()
            
            # Update model info
            self.monitor.set_model_info(False, "N/A", "N/A", "N/A")
            
            # Update status
            self.status_label.setText("Model unloaded successfully.")
            
        except Exception as e:
            self.status_label.setText(f"Error unloading model: {e}")
    
    def clear_cache(self):
        """Clear CUDA cache."""
        try:
            if HAS_TORCH and torch.cuda.is_available():
                torch.cuda.empty_cache()
                self.status_label.setText("CUDA cache cleared.")
            else:
                self.status_label.setText("No CUDA device available.")
        except Exception as e:
            self.status_label.setText(f"Error clearing cache: {e}")
    
    def run_garbage_collection(self):
        """Run Python garbage collection."""
        try:
            import gc
            gc.collect()
            self.status_label.setText("Garbage collection completed.")
        except Exception as e:
            self.status_label.setText(f"Error running garbage collection: {e}")


# Function to create a resource monitor tab for the browser
def create_resource_monitor_tab(browser):
    """Create a resource monitor tab for the browser."""
    if not HAS_PYQT:
        return None
    
    # Create the resource monitor widget
    monitor_widget = ResourceMonitorWidget()
    
    # Add required dependencies to requirements.txt if not already present
    try:
        import pkg_resources
        
        required_packages = {
            "psutil": ">=5.9.0",
            "GPUtil": ">=1.4.0"
        }
        
        missing_packages = []
        for package, version in required_packages.items():
            try:
                pkg_resources.get_distribution(package)
            except pkg_resources.DistributionNotFound:
                missing_packages.append(f"{package}{version}")
        
        if missing_packages:
            print(f"Installing required packages for resource monitor: {', '.join(missing_packages)}")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
    except Exception as e:
        print(f"Error checking dependencies: {e}")
    
    return monitor_widget
