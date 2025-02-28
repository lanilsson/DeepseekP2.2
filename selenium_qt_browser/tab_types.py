"""
Tab Types Module - Defines the tab types used in the browser

This module contains the TabType enum which defines the different
types of tabs that can be created in the browser.
"""

from enum import Enum, auto

class TabType(Enum):
    """Enum for the different types of tabs."""
    BROWSER = auto()
    CHAT = auto()
    TERMINAL = auto()
    NOTEPAGE = auto()
    NOTEPAGE_EXC = auto()
    RESOURCE_MONITOR = auto()  # Tab for monitoring system resources and model performance
    AI_BROWSER = auto()  # Tab for controlling the AI browser middleware