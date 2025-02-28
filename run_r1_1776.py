#!/usr/bin/env python3
"""
R1-1776 Model Setup Script

This script downloads and sets up the r1-1776 model from Hugging Face.
It handles dependencies installation, model downloading, and prepares it for local inference.

The script automatically detects your hardware capabilities and configures
the model for optimal performance on your system.
"""

import os
import sys
import argparse
import subprocess
import logging
import importlib.util
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Model information
MODEL_ID = "Roo-AI/r1-1776"
DEFAULT_MODEL_DIR = os.path.join(os.path.expanduser("~"), ".cache", "r1-1776")

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        "transformers>=4.30.0",
        "torch>=2.0.0",
        "accelerate>=0.20.0",
        "sentencepiece>=0.1.99",
        "protobuf>=3.20.0",
        "bitsandbytes>=0.41.0",  # For quantization support
        "safetensors>=0.3.1",    # For safe model loading
        "psutil>=5.9.0"          # For hardware detection
    ]
    
    logger.info("Checking dependencies...")
    
    missing_packages = []
    for package in required_packages:
        package_name = package.split('>=')[0]
        try:
            __import__(package_name)
            logger.info(f"✓ {package_name} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"✗ {package_name} is not installed")
    
    if missing_packages:
        logger.info("Installing missing dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            logger.info("All dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            logger.info("Please install the following packages manually:")
            for package in missing_packages:
                logger.info(f"  - {package}")
            sys.exit(1)
    else:
        logger.info("All dependencies are already installed")

def download_model(model_dir, use_8bit=False, use_4bit=False, force_cpu=False, verbose=False):
    """Download the model from Hugging Face."""
    logger.info(f"Downloading model {MODEL_ID}...")
    
    # Import here to ensure dependencies are installed
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    
    # Create model directory if it doesn't exist
    os.makedirs(model_dir, exist_ok=True)
    
    # Download tokenizer
    logger.info("Downloading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    tokenizer.save_pretrained(model_dir)
    logger.info(f"Tokenizer saved to {model_dir}")
    
    # Check if r1_1776_utils.py exists and is importable
    utils_path = os.path.join(os.path.dirname(__file__), "r1_1776_utils.py")
    use_utils = os.path.exists(utils_path)
    
    if use_utils:
        try:
            # Import the utilities module for hardware detection
            from r1_1776_utils import get_system_info, determine_optimal_config
            
            # Get system information
            if verbose:
                logger.info("Analyzing system hardware...")
                system_info = get_system_info()
                logger.info("System information:")
                for key, value in system_info.items():
                    if key != "gpu_info":  # Skip detailed GPU info in the summary
                        logger.info(f"  {key}: {value}")
                if system_info["gpu_info"]:
                    logger.info("  GPU details:")
                    for gpu in system_info["gpu_info"]:
                        logger.info(f"    {gpu['name']} ({gpu['memory_gb']} GB)")
            else:
                system_info = get_system_info()
            
            # Determine optimal configuration based on hardware
            config = determine_optimal_config(system_info)
            
            # Override with command line arguments if specified
            if use_8bit:
                logger.info("Overriding with 8-bit quantization (user specified)")
                config["load_in_8bit"] = True
                config["load_in_4bit"] = False
            elif use_4bit:
                logger.info("Overriding with 4-bit quantization (user specified)")
                config["load_in_8bit"] = False
                config["load_in_4bit"] = True
                config["bnb_4bit_compute_dtype"] = torch.float16
                config["bnb_4bit_quant_type"] = "nf4"
            
            if force_cpu:
                logger.info("Overriding with CPU usage (user specified)")
                config["device_map"] = "cpu"
                config["use_cpu"] = True
            
            if verbose:
                logger.info("Using configuration:")
                for key, value in config.items():
                    logger.info(f"  {key}: {value}")
            
            # Extract quantization and device settings
            load_kwargs = {k: v for k, v in config.items() if k not in ["use_cpu", "offload_folder"]}
            
        except ImportError as e:
            logger.warning(f"Could not import utilities module: {e}")
            logger.info("Falling back to basic configuration")
            use_utils = False
    
    if not use_utils:
        # Fallback to basic configuration if utils module is not available
        logger.info("Using basic configuration without hardware optimization")
        
        # Determine quantization settings
        if use_8bit and use_4bit:
            logger.warning("Both 8-bit and 4-bit quantization specified. Using 4-bit as it's more efficient.")
            use_8bit = False
        
        load_kwargs = {
            "torch_dtype": torch.float16,
            "device_map": "cpu" if force_cpu else "auto",
        }
        
        if use_8bit:
            logger.info("Using 8-bit quantization for reduced memory usage")
            load_kwargs["load_in_8bit"] = True
        elif use_4bit:
            logger.info("Using 4-bit quantization for minimal memory usage")
            load_kwargs["load_in_4bit"] = True
            load_kwargs["bnb_4bit_compute_dtype"] = torch.float16
            load_kwargs["bnb_4bit_quant_type"] = "nf4"
    
    # Download model with appropriate configuration
    logger.info("Downloading model weights (this may take a while)...")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            **load_kwargs
        )
        model.save_pretrained(model_dir)
        logger.info(f"Model saved to {model_dir}")
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        sys.exit(1)
    
    return tokenizer, model

def test_model(model_dir, tokenizer, model):
    """Test the model with a simple prompt."""
    logger.info("Testing model with a simple prompt...")
    
    try:
        # Check if r1_1776_utils.py exists and is importable
        utils_path = os.path.join(os.path.dirname(__file__), "r1_1776_utils.py")
        if os.path.exists(utils_path):
            try:
                # Use the utility function for text generation
                from r1_1776_utils import generate_text
                
                prompt = "Hello, I'm interested in learning about artificial intelligence. Can you explain what it is?"
                logger.info("Generating response (this may take a moment)...")
                
                response = generate_text(
                    tokenizer=tokenizer,
                    model=model,
                    prompt=prompt,
                    max_new_tokens=100,
                    temperature=0.7,
                    do_sample=True
                )
                
                logger.info(f"Model response: {prompt}{response}")
                logger.info("Model test completed successfully")
                
            except ImportError:
                # Fallback to direct generation if utils module is not importable
                _test_model_direct(tokenizer, model)
        else:
            # Fallback to direct generation if utils module doesn't exist
            _test_model_direct(tokenizer, model)
            
    except Exception as e:
        logger.error(f"Error testing model: {e}")
        logger.warning("Model download may have been incomplete or corrupted")
        logger.info("Please try running the script again")

def _test_model_direct(tokenizer, model):
    """Direct model testing without using the utils module."""
    import torch
    
    prompt = "Hello, I'm interested in learning about artificial intelligence. Can you explain what it is?"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    logger.info("Generating response (this may take a moment)...")
    with torch.no_grad():
        outputs = model.generate(
            inputs["input_ids"],
            max_new_tokens=100,
            temperature=0.7,
            do_sample=True
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    logger.info(f"Model response: {response}")
    logger.info("Model test completed successfully")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='R1-1776 Model Setup',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Model location options
    model_group = parser.add_argument_group('Model Location')
    model_group.add_argument('--model-dir', type=str, default=DEFAULT_MODEL_DIR,
                        help=f'Directory to save the model')
    
    # Hardware configuration options
    hw_group = parser.add_argument_group('Hardware Configuration')
    hw_group.add_argument('--use-8bit', action='store_true',
                        help='Load model in 8-bit quantization for reduced memory usage')
    hw_group.add_argument('--use-4bit', action='store_true',
                        help='Load model in 4-bit quantization for minimal memory usage')
    hw_group.add_argument('--force-cpu', action='store_true',
                        help='Force CPU usage even if GPU is available')
    
    # Testing options
    test_group = parser.add_argument_group('Testing Options')
    test_group.add_argument('--skip-test', action='store_true',
                        help='Skip testing the model after download')
    test_group.add_argument('--verbose', action='store_true',
                        help='Show detailed information about hardware and configuration')
    
    return parser.parse_args()

def main():
    """Main function to download and set up the model."""
    args = parse_arguments()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting R1-1776 model setup")
    
    # Check and install dependencies
    check_dependencies()
    
    # Download model
    tokenizer, model = download_model(
        args.model_dir,
        use_8bit=args.use_8bit,
        use_4bit=args.use_4bit,
        force_cpu=args.force_cpu,
        verbose=args.verbose
    )
    
    # Test model if not skipped
    if not args.skip_test:
        test_model(args.model_dir, tokenizer, model)
    
    logger.info(f"R1-1776 model setup completed successfully")
    logger.info(f"Model saved to: {args.model_dir}")
    
    # Check if r1_1776_utils.py exists
    utils_path = os.path.join(os.path.dirname(__file__), "r1_1776_utils.py")
    if os.path.exists(utils_path):
        logger.info("\nTo use the model with automatic hardware optimization:")
        logger.info("```python")
        logger.info("from r1_1776_utils import load_model, generate_text")
        logger.info(f"tokenizer, model = load_model('{args.model_dir}')")
        logger.info("response = generate_text(tokenizer, model, 'Your prompt here')")
        logger.info("print(response)")
        logger.info("```")
    else:
        logger.info("\nTo use the model in your Python code:")
        logger.info("```python")
        logger.info("from transformers import AutoTokenizer, AutoModelForCausalLM")
        logger.info(f"tokenizer = AutoTokenizer.from_pretrained('{args.model_dir}')")
        logger.info("model = AutoModelForCausalLM.from_pretrained(")
        logger.info(f"    '{args.model_dir}',")
        logger.info("    torch_dtype=torch.float16,")
        logger.info("    device_map='auto'")
        logger.info(")")
        logger.info("```")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)