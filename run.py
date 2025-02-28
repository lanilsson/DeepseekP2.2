#!/usr/bin/env python3
"""
Run Script for Selenium Qt Browser

This script provides a convenient way to run the Selenium Qt Browser
without installing it as a package.
"""

import os
import sys
import argparse



# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the main module
from selenium_qt_browser.main import main, parse_arguments

if __name__ == "__main__":
    # Run the main function
    main()