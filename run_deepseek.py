#!/usr/bin/env python3
"""
Deepseek Dual Models Launcher

This script provides a convenient way to run the Deepseek Dual Models application
without having to navigate to the deepseek_dual_models directory.
"""

import os
import sys
import argparse

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Deepseek Dual Models Launcher')
    parser.add_argument('--model1', type=str, help='Path to first model')
    parser.add_argument('--model2', type=str, help='Path to second model')
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Import the main function from the Deepseek Dual Models module
    try:
        from deepseek_dual_models.run_deepseek_models import main
        
        # Run the main function
        main()
    except ImportError as e:
        print(f"Error importing Deepseek Dual Models: {e}")
        print("Make sure you have installed all required dependencies.")
        print("Try running: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error running Deepseek Dual Models: {e}")
        sys.exit(1)