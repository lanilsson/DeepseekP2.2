#!/usr/bin/env python3
"""
Selenium Qt Browser - Main Application Entry Point

This module initializes the PyQt6 application and launches the main browser window
with direct controller integration.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication, Qt

# Import local modules
from selenium_qt_browser.browser import BrowserWindow
from selenium_qt_browser.controller import get_controller
from selenium_qt_browser.login import show_login_screen

# Load environment variables from .env file if it exists
load_dotenv()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Jordan AI Browser')
    parser.add_argument('--url', type=str, help='URL to open on startup')
    parser.add_argument('--profile', type=str, help='Browser profile to use')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--no-login', action='store_true', help='Skip the login screen')
    return parser.parse_args()

def setup_application():
    """Set up the Qt application with proper settings."""
    # Set application metadata
    QCoreApplication.setApplicationName("Jordan AI Browser")
    QCoreApplication.setOrganizationName("JordanAI")
    QCoreApplication.setOrganizationDomain("jordanai.example.com")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Jordan AI Browser")
    
    # Set application style
    app.setStyle("Fusion")
    
    return app

def launch_browser(args):
    """Launch the main browser window."""
    # Create and show the main browser window
    browser_window = BrowserWindow(
        start_url=args.url,
        profile_name=args.profile,
        headless=args.headless
    )
    browser_window.show()
    
    # Initialize the controller
    controller = get_controller(browser_window)
    
    # Make the controller available globally
    sys.modules['selenium_qt_browser'].controller = controller
    
    print("Jordan AI Browser started")
    print("Controller available for direct programmatic access")
    print("Example usage from Python:")
    print("  from selenium_qt_browser.controller import get_controller")
    print("  controller = get_controller()")
    print("  controller.navigate('https://example.com')")
    print("  controller.get_page_info()")

def main():
    """Main application entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up the Qt application
    app = setup_application()
    
    if args.no_login:
        # Skip login screen if requested
        launch_browser(args)
    else:
        # Show login screen first, then launch browser
        login_screen = show_login_screen(lambda: launch_browser(args))
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()