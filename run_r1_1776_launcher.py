#!/usr/bin/env python3
"""
R1-1776 Model Launcher

This script provides a convenient way to run the R1-1776 model setup
without having to remember all the command line options.

It automatically detects your hardware capabilities and configures
the model for optimal performance on your system.
"""

import os
import sys
import argparse

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='R1-1776 Model Launcher',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Model location options
    model_group = parser.add_argument_group('Model Location')
    model_group.add_argument('--model-dir', type=str,
                        default=os.path.join(os.path.expanduser("~"), ".cache", "r1-1776"),
                        help='Directory to save the model')
    
    # Hardware configuration options
    hw_group = parser.add_argument_group('Hardware Configuration')
    hw_group.add_argument('--use-8bit', action='store_true',
                        help='Load model in 8-bit quantization for reduced memory usage')
    hw_group.add_argument('--use-4bit', action='store_true',
                        help='Load model in 4-bit quantization for minimal memory usage')
    hw_group.add_argument('--force-cpu', action='store_true',
                        help='Force CPU usage even if GPU is available')
    hw_group.add_argument('--auto-detect', action='store_true', default=True,
                        help='Automatically detect and use optimal hardware configuration')
    
    # Testing options
    test_group = parser.add_argument_group('Testing Options')
    test_group.add_argument('--skip-test', action='store_true',
                        help='Skip testing the model after download')
    test_group.add_argument('--verbose', action='store_true',
                        help='Show detailed information about hardware and configuration')
    
    # Example usage
    example_group = parser.add_argument_group('Example Usage')
    example_group.add_argument('--run-example', action='store_true',
                        help='Run the interactive example after setup is complete')
    
    return parser.parse_args()

def print_hardware_info():
    """Print information about the system hardware."""
    try:
        # Import the utilities module
        from r1_1776_utils import get_system_info
        
        print("\nHardware Information:")
        print("=" * 50)
        
        system_info = get_system_info()
        for key, value in system_info.items():
            if key != "gpu_info":  # Skip detailed GPU info in the summary
                print(f"  {key}: {value}")
                
        if system_info["gpu_info"]:
            print("  GPU details:")
            for gpu in system_info["gpu_info"]:
                print(f"    {gpu['name']} ({gpu['memory_gb']} GB)")
        
        print("=" * 50)
        print()
    except ImportError:
        # If the utils module isn't available yet, skip hardware info
        pass

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Print hardware information if verbose
    if args.verbose:
        print_hardware_info()
    
    # Import the main function from the R1-1776 module
    try:
        from run_r1_1776 import main
        
        # Override sys.argv to pass arguments to the main script
        sys.argv = [sys.argv[0]]
        if args.model_dir:
            sys.argv.extend(['--model-dir', args.model_dir])
        if args.use_8bit:
            sys.argv.append('--use-8bit')
        if args.use_4bit:
            sys.argv.append('--use-4bit')
        if args.force_cpu:
            sys.argv.append('--force-cpu')
        if args.skip_test:
            sys.argv.append('--skip-test')
        if args.verbose:
            sys.argv.append('--verbose')
        
        # Run the main function
        main()
        
        # Run the example if requested
        if args.run_example:
            print("\nRunning interactive example...")
            try:
                import subprocess
                example_path = os.path.join(os.path.dirname(__file__), "examples", "r1_1776_example.py")
                example_args = [sys.executable, example_path]
                if args.model_dir:
                    example_args.extend(["--model-dir", args.model_dir])
                if args.verbose:
                    example_args.append("--verbose")
                if args.force_cpu:
                    example_args.append("--force-cpu")
                if args.use_8bit:
                    example_args.append("--force-8bit")
                if args.use_4bit:
                    example_args.append("--force-4bit")
                
                subprocess.run(example_args)
            except Exception as e:
                print(f"Error running example: {e}")
    except ImportError as e:
        print(f"Error importing R1-1776 model setup: {e}")
        print("Make sure you have installed all required dependencies.")
        print("Try running: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error running R1-1776 model setup: {e}")
        sys.exit(1)