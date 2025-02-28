"""
Browser Module - Implements the main browser window and functionality

This module contains the BrowserWindow class which provides the main UI
and browser functionality using PyQt6 and QWebEngineView, along with
AI chat and terminal functionality.
"""

import os
import json
from pathlib import Path
from PyQt6.QtCore import QUrl, Qt, QSize, pyqtSlot, QSettings
from PyQt6.QtWidgets import (
    QMainWindow, QToolBar, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QTabWidget,
    QMenu, QMenuBar, QStatusBar, QDialog, QFileDialog,
    QMessageBox, QLabel, QProgressBar, QSplitter, QComboBox,
    QApplication, QInputDialog
)
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage

from selenium_qt_browser.tab_types import TabType
from selenium_qt_browser.automation import AutomationPanel
from selenium_qt_browser.chat import AIChatTab
from selenium_qt_browser.terminal import TerminalTab
from selenium_qt_browser.notepage import NotePage
from selenium_qt_browser.notepage_exc import NotePageExc
from selenium_qt_browser.session_manager import SessionManager
from selenium_qt_browser.resource_monitor import ResourceMonitorWidget, create_resource_monitor_tab
from selenium_qt_browser.ai_browser_tab import AIBrowserTab

class BrowserTab(QWidget):
    """A single browser tab containing a web view and related controls."""
    
    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.tab_type = TabType.BROWSER
        
        # Create web view with the specified profile
        self.web_view = QWebEngineView()
        self.web_view.setPage(QWebEnginePage(profile, self.web_view))
        
        # Set up page settings
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        
        # Connect signals
        self.web_view.loadStarted.connect(self.on_load_started)
        self.web_view.loadProgress.connect(self.on_load_progress)
        self.web_view.loadFinished.connect(self.on_load_finished)
        self.web_view.titleChanged.connect(self.on_title_changed)
        self.web_view.urlChanged.connect(self.on_url_changed)
        
        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(self.web_view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # Initialize progress bar (will be shown in status bar)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(1)
        self.progress_bar.setMaximumWidth(120)
        self.progress_bar.setTextVisible(False)
        
    def navigate_to(self, url):
        """Navigate to the specified URL."""
        if not url.startswith(('http://', 'https://', 'file://')):
            url = 'https://' + url
        self.web_view.load(QUrl(url))
        
    def on_load_started(self):
        """Handle the start of page loading."""
        if self.parent:
            self.parent.statusBar().addWidget(self.progress_bar)
            self.progress_bar.show()
            
    def on_load_progress(self, progress):
        """Update progress bar during page loading."""
        self.progress_bar.setValue(progress)
        
    def on_load_finished(self, success):
        """Handle the completion of page loading."""
        if self.parent:
            self.parent.statusBar().removeWidget(self.progress_bar)
        
    def on_title_changed(self, title):
        """Update tab title when page title changes."""
        if self.parent and isinstance(self.parent, BrowserWindow):
            index = self.parent.tab_widget.indexOf(self)
            if index != -1:
                self.parent.tab_widget.setTabText(index, title[:20] + '...' if len(title) > 20 else title)
                
    def on_url_changed(self, url):
        """Update address bar when URL changes."""
        if self.parent and isinstance(self.parent, BrowserWindow):
            self.parent.address_bar.setText(url.toString())
            
    def current_url(self):
        """Get the current URL."""
        return self.web_view.url().toString()
    
    def current_page(self):
        """Get the current QWebEnginePage."""
        return self.web_view.page()


class BrowserWindow(QMainWindow):
    """Main browser window with tabs and controls."""
    
    def __init__(self, start_url=None, profile_name=None, headless=False, script_path=None):
        super().__init__()
        
        # Initialize variables
        self.profile_name = profile_name or "default"
        self.headless = headless
        # script_path parameter kept for compatibility but not used
        self.start_url = start_url or "https://www.google.com"
        
        # Initialize session manager for auto-loading previous session
        self.session_manager = SessionManager(self)
        
        # Set up the browser profile for persistence
        self.setup_profile()
        # Set up the UI
        self.setup_ui()
        
        # Try to load previous session, or create default tabs if none exists
        if not self.session_manager.load_last_session(self):
            # Create initial tabs (one of each type) if no previous session
            self.add_new_tab(self.start_url)  # Web browser tab
            self.add_new_chat_tab()           # AI chat tab
            self.add_new_terminal_tab()       # Terminal tab
            
            # Set the first tab (browser) as active
            self.tab_widget.setCurrentIndex(0)
            self.current_tab().navigate_to(self.start_url)
    
    def setup_profile(self):
        """Set up the browser profile for persistent storage."""
        # Create profile directory if it doesn't exist
        profile_dir = Path.home() / ".selenium_qt_browser" / "profiles" / self.profile_name
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a persistent profile
        self.profile = QWebEngineProfile(self.profile_name)
        self.profile.setPersistentStoragePath(str(profile_dir / "storage"))
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.profile.setCachePath(str(profile_dir / "cache"))
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        
        # Enable developer tools (if available)
        # Note: DeveloperExtrasEnabled is not available in this version of PyQt6
        # Enable other useful settings
        settings = self.profile.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
    
    def setup_ui(self):
        """Set up the main window UI."""
        # Set window properties
        self.setWindowTitle("Jordan AI")
        self.setMinimumSize(1000, 700)
        
        # Apply modern dark theme to the entire application
        self.apply_dark_theme()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create navigation toolbar
        nav_toolbar = QToolBar("Navigation")
        nav_toolbar.setMovable(False)
        nav_toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(nav_toolbar)
        
        # Add navigation buttons
        self.back_button = QAction("Back", self)
        self.back_button.triggered.connect(self.navigate_back)
        nav_toolbar.addAction(self.back_button)
        
        self.forward_button = QAction("Forward", self)
        self.forward_button.triggered.connect(self.navigate_forward)
        nav_toolbar.addAction(self.forward_button)
        
        self.reload_button = QAction("Reload", self)
        self.reload_button.triggered.connect(self.reload_page)
        nav_toolbar.addAction(self.reload_button)
        
        self.home_button = QAction("Home", self)
        self.home_button.triggered.connect(self.navigate_home)
        nav_toolbar.addAction(self.home_button)
        
        # Add address bar
        nav_toolbar.addSeparator()
        self.address_bar = QLineEdit()
        self.address_bar.returnPressed.connect(self.navigate_to_url)
        nav_toolbar.addWidget(self.address_bar)
        
        # Add tab type selector
        nav_toolbar.addSeparator()
        tab_type_label = QLabel("New Tab Type:")
        nav_toolbar.addWidget(tab_type_label)
        self.tab_type_selector = QComboBox()
        self.tab_type_selector.addItems(["Web Browser", "AI Chat", "Terminal", "NotePage", "NotePage Exc", "Resource Monitor", "AI Browser"])
        nav_toolbar.addWidget(self.tab_type_selector)
        
        add_tab_button = QPushButton("+")
        add_tab_button.setToolTip("Add new tab of selected type")
        add_tab_button.clicked.connect(self.add_new_tab_of_selected_type)
        nav_toolbar.addWidget(add_tab_button)
        
        # No session selector - we'll just load the previous session automatically
        
        # Create tab widget for browser tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        # Add tab widget directly to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Create status bar
        self.setStatusBar(QStatusBar())
        
        # Create menu bar
        self.create_menus()
        
        # Keep automation_panel attribute for compatibility
        self.automation_panel = None
    
    def create_menus(self):
        """Create the application menu bar."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        
        # New tab submenu
        new_tab_menu = QMenu("&New Tab", self)
        file_menu.addMenu(new_tab_menu)
        
        new_browser_tab_action = QAction("New &Browser Tab", self)
        new_browser_tab_action.setShortcut(QKeySequence.StandardKey.AddTab)
        new_browser_tab_action.triggered.connect(self.add_new_tab)
        new_tab_menu.addAction(new_browser_tab_action)
        
        new_chat_tab_action = QAction("New &AI Chat Tab", self)
        new_chat_tab_action.triggered.connect(self.add_new_chat_tab)
        new_tab_menu.addAction(new_chat_tab_action)
        
        new_terminal_tab_action = QAction("New &Terminal Tab", self)
        new_terminal_tab_action.triggered.connect(self.add_new_terminal_tab)
        new_tab_menu.addAction(new_terminal_tab_action)
        
        new_notepage_tab_action = QAction("New &NotePage Tab", self)
        new_notepage_tab_action.triggered.connect(self.add_new_notepage_tab)
        new_tab_menu.addAction(new_notepage_tab_action)
        new_notepage_exc_tab_action = QAction("New NotePage &Exc Tab", self)
        new_notepage_exc_tab_action.triggered.connect(self.add_new_notepage_exc_tab)
        new_tab_menu.addAction(new_notepage_exc_tab_action)
        
        new_resource_monitor_tab_action = QAction("New &Resource Monitor Tab", self)
        new_resource_monitor_tab_action.triggered.connect(self.add_new_resource_monitor_tab)
        new_tab_menu.addAction(new_resource_monitor_tab_action)
        
        new_ai_browser_tab_action = QAction("New AI &Browser Control Tab", self)
        new_ai_browser_tab_action.triggered.connect(self.add_new_ai_browser_tab)
        new_tab_menu.addAction(new_ai_browser_tab_action)
        
        close_tab_action = QAction("&Close Tab", self)
        close_tab_action.setShortcut(QKeySequence.StandardKey.Close)
        close_tab_action.triggered.connect(lambda: self.close_tab(self.tab_widget.currentIndex()))
        file_menu.addAction(close_tab_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = self.menuBar().addMenu("&Edit")
        
        # View menu
        view_menu = self.menuBar().addMenu("&View")
        
        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    def add_new_tab_of_selected_type(self):
        """Add a new tab of the selected type."""
        tab_type_text = self.tab_type_selector.currentText()
        
        if tab_type_text == "Web Browser":
            return self.add_new_tab()
        elif tab_type_text == "AI Chat":
            return self.add_new_chat_tab()
        elif tab_type_text == "Terminal":
            return self.add_new_terminal_tab()
        elif tab_type_text == "NotePage":
            return self.add_new_notepage_tab()
        elif tab_type_text == "NotePage Exc":
            return self.add_new_notepage_exc_tab()
        elif tab_type_text == "Resource Monitor":
            return self.add_new_resource_monitor_tab()
        elif tab_type_text == "AI Browser":
            return self.add_new_ai_browser_tab()
    
    def add_new_tab(self, url=None):
        """Add a new browser tab."""
        tab = BrowserTab(self.profile, self)
        index = self.tab_widget.addTab(tab, "Web Browser")
        self.tab_widget.setCurrentIndex(index)
        
        # If no URL is provided, use the default start URL (Google)
        if not url:
            url = self.start_url
        
        # Navigate to the URL
        tab.navigate_to(url)
        
        return tab
    
    def add_new_chat_tab(self):
        """Add a new AI chat tab."""
        tab = AIChatTab(self)
        index = self.tab_widget.addTab(tab, "AI Chat")
        self.tab_widget.setCurrentIndex(index)
        return tab
    
    def add_new_terminal_tab(self):
        """Add a new terminal tab."""
        tab = TerminalTab(self)
        index = self.tab_widget.addTab(tab, "Terminal")
        self.tab_widget.setCurrentIndex(index)
        return tab
    
    def add_new_notepage_tab(self):
        """Add a new note page tab."""
        tab = NotePage(self)
        index = self.tab_widget.addTab(tab, "NotePage")
        self.tab_widget.setCurrentIndex(index)
        return tab
    
    def add_new_notepage_exc_tab(self):
        """Add a new spreadsheet tab."""
        tab = NotePageExc(self)
        index = self.tab_widget.addTab(tab, "NotePage Exc")
        self.tab_widget.setCurrentIndex(index)
        return tab
    
    def add_new_resource_monitor_tab(self):
        """Add a new resource monitor tab."""
        tab = ResourceMonitorWidget(self)
        tab.tab_type = TabType.RESOURCE_MONITOR
        index = self.tab_widget.addTab(tab, "Resource Monitor")
        self.tab_widget.setCurrentIndex(index)
        return tab
    
    def add_new_ai_browser_tab(self):
        """Add a new AI browser tab."""
        tab = AIBrowserTab(self)
        index = self.tab_widget.addTab(tab, "AI Browser")
        self.tab_widget.setCurrentIndex(index)
        return tab
    
    def scroll_to_bottom(self, widget):
        """Scroll a widget to the bottom."""
        if hasattr(widget, 'verticalScrollBar'):
            scrollbar = widget.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def close_tab(self, index):
        """Close the tab at the specified index."""
        if self.tab_widget.count() > 1:
            # Get the tab before removing it
            tab = self.tab_widget.widget(index)
            
            # Special handling for terminal tabs
            if hasattr(tab, 'tab_type') and tab.tab_type == TabType.TERMINAL:
                # Make sure to terminate any running processes
                if hasattr(tab, 'process') and tab.process:
                    tab.process.terminate()
            
            self.tab_widget.removeTab(index)
        else:
            # Don't close the last tab, navigate to home instead if it's a browser tab
            current = self.current_tab()
            if hasattr(current, 'tab_type') and current.tab_type == TabType.BROWSER:
                current.navigate_to(self.start_url)
            elif hasattr(current, 'tab_type') and current.tab_type == TabType.CHAT:
                # For chat tab, just keep it open
                pass
            elif hasattr(current, 'tab_type') and current.tab_type == TabType.TERMINAL:
                # For terminal tab, just keep it open
                pass
            elif hasattr(current, 'tab_type') and current.tab_type == TabType.RESOURCE_MONITOR:
                # For resource monitor tab, just keep it open
                pass
            elif hasattr(current, 'tab_type') and current.tab_type == TabType.AI_BROWSER:
                # For AI browser tab, just keep it open
                pass
            else:
                # Default to creating a new browser tab
                self.tab_widget.removeTab(0)
                self.add_new_tab(self.start_url)
    
    def current_tab(self):
        """Get the current tab."""
        return self.tab_widget.currentWidget()
    
    def navigate_to_url(self):
        """Navigate to the URL in the address bar."""
        current = self.current_tab()
        if hasattr(current, 'tab_type') and current.tab_type == TabType.BROWSER:
            url = self.address_bar.text()
            current.navigate_to(url)
    
    def navigate_back(self):
        """Navigate back in the current tab."""
        current = self.current_tab()
        if hasattr(current, 'tab_type') and current.tab_type == TabType.BROWSER:
            current.web_view.back()
    
    def navigate_forward(self):
        """Navigate forward in the current tab."""
        current = self.current_tab()
        if hasattr(current, 'tab_type') and current.tab_type == TabType.BROWSER:
            current.web_view.forward()
    
    def reload_page(self):
        """Reload the current page."""
        current = self.current_tab()
        if hasattr(current, 'tab_type') and current.tab_type == TabType.BROWSER:
            current.web_view.reload()
    
    def navigate_home(self):
        """Navigate to the home page."""
        current = self.current_tab()
        if hasattr(current, 'tab_type') and current.tab_type == TabType.BROWSER:
            current.navigate_to(self.start_url)
    
    def toggle_automation_panel(self):
        """Stub implementation of toggle_automation_panel."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Feature Removed",
            "The automation functionality has been removed from this version."
        )
    
    def load_automation_script(self):
        """Stub implementation of load_automation_script."""
        self.toggle_automation_panel()
    
    def run_automation_script(self):
        """Stub implementation of run_automation_script."""
        self.toggle_automation_panel()
    
    def show_about_dialog(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About Jordan AI",
            "Jordan AI\n\n"
            "A Python application that provides a PyQt6-based web browser with AI capabilities.\n\n"
            "Version 1.0.0"
        )
    
    def apply_dark_theme(self):
        """Apply a modern dark theme to the entire application."""
        from PyQt6.QtGui import QPalette
        
        # Create a dark palette
        palette = QPalette()
        
        # Set colors for different UI elements
        palette.setColor(QPalette.ColorRole.Window, QColor(18, 18, 18))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Text, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Link, QColor(66, 133, 244))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(66, 133, 244))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(240, 240, 240))
        
        # Apply the palette to the application
        QApplication.instance().setPalette(palette)
        
        # Set stylesheet for additional styling
        QApplication.instance().setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #121212;
            }
            
            QTabWidget::pane {
                border: 1px solid #3a3a3a;
                background-color: #1e1e1e;
            }
            
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 8px 12px;
                border: 1px solid #3a3a3a;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #353535;
            }
            
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 4px;
            }
            
            QPushButton {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px 12px;
            }
            
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            
            QPushButton:pressed {
                background-color: #4a4a4a;
            }
            
            QToolBar {
                background-color: #1e1e1e;
                border-bottom: 1px solid #3a3a3a;
                spacing: 6px;
            }
            
            QStatusBar {
                background-color: #1e1e1e;
                color: #cccccc;
            }
            
            QMenuBar {
                background-color: #1e1e1e;
                color: #f0f0f0;
            }
            
            QMenuBar::item:selected {
                background-color: #3d3d3d;
            }
            
            QMenu {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid #3c3c3c;
            }
            
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
            
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #5a5a5a;
                min-height: 20px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #6a6a6a;
            }
            
            QScrollBar:horizontal {
                background-color: #1e1e1e;
                height: 12px;
                margin: 0px;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #5a5a5a;
                min-width: 20px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #6a6a6a;
            }
            
            QComboBox {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 4px;
            }
            
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left: 1px solid #3c3c3c;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #f0f0f0;
                selection-background-color: #3d3d3d;
            }
        """)
    
    # Session management methods removed - we now just auto-save/load the last session
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save the current session before closing
        try:
            self.session_manager.save_session(self)
        except Exception as e:
            print(f"Error saving session: {e}")
        
        event.accept()