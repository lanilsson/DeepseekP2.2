#!/usr/bin/env python3
"""
R1-1776 Model Example

This script demonstrates how to use the R1-1776 model after it has been downloaded.
It provides a simple interactive chat interface where you can ask questions and
get responses from the model.

This example uses the r1_1776_utils module for smart model initialization
that adapts to your hardware capabilities.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the parent directory to the Python path to import the utils module
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='R1-1776 Model Example')
    parser.add_argument('--model-dir', type=str,
                        default=os.path.join(os.path.expanduser("~"), ".cache", "r1-1776"),
                        help='Directory where the model is saved')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose output with hardware details')
    parser.add_argument('--force-cpu', action='store_true',
                        help='Force CPU usage even if GPU is available')
    parser.add_argument('--force-8bit', action='store_true',
                        help='Force 8-bit quantization')
    parser.add_argument('--force-4bit', action='store_true',
                        help='Force 4-bit quantization')
    return parser.parse_args()

def main():
    """Main function to run the example."""
    args = parse_arguments()
    
    try:
        # Import the utilities module
        from r1_1776_utils import load_model, generate_text, get_system_info
        
        # Print system info if verbose
        if args.verbose:
            print("System Information:")
            system_info = get_system_info()
            for key, value in system_info.items():
                if key != "gpu_info":  # Skip detailed GPU info in the summary
                    print(f"  {key}: {value}")
                    
            if system_info["gpu_info"]:
                print("  GPU details:")
                for gpu in system_info["gpu_info"]:
                    print(f"    {gpu['name']} ({gpu['memory_gb']} GB)")
            print()
        
        # Create a custom configuration if any force flags are set
        force_config = None
        if args.force_cpu or args.force_8bit or args.force_4bit:
            import torch
            force_config = {
                "device_map": "cpu" if args.force_cpu else "auto",
                "torch_dtype": torch.float16,
                "load_in_8bit": args.force_8bit,
                "load_in_4bit": args.force_4bit,
            }
            
            if args.force_4bit:
                force_config["bnb_4bit_compute_dtype"] = torch.float16
                force_config["bnb_4bit_quant_type"] = "nf4"
                
            print(f"Using forced configuration: {'CPU' if args.force_cpu else 'GPU'} with "
                  f"{'4-bit' if args.force_4bit else '8-bit' if args.force_8bit else 'FP16'} precision")
        
        # Load the model with smart initialization
        print(f"Loading model from {args.model_dir}...")
        print("The system will automatically select the optimal configuration for your hardware.")
        print("This may take a moment depending on your hardware capabilities.")
        
        tokenizer, model = load_model(
            model_dir=args.model_dir,
            force_config=force_config,
            verbose=args.verbose
        )
        
        print("\nModel loaded successfully!")
        print("=" * 50)
        print("R1-1776 Interactive Chat")
        print("Type your questions and press Enter. Type 'exit' to quit.")
        print("=" * 50)
        
        # Interactive chat loop
        while True:
            # Get user input
            user_input = input("\nYou: ")
            
            # Check if user wants to exit
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
            
            # Generate response using the utility function
            print("\nGenerating response...")
            model_response = generate_text(
                tokenizer=tokenizer,
                model=model,
                prompt=user_input,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
                do_sample=True
            )
            
            print(f"\nR1-1776: {model_response}")
    
    except ImportError as e:
        print(f"Error: {e}")
        print("Please make sure you have installed all required dependencies:")
        print("  pip install transformers torch accelerate bitsandbytes psutil")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)