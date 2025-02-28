#!/usr/bin/env python3
"""
R1-1776 Model Utilities

This module provides utility functions for working with the R1-1776 model,
including smart initialization that adapts to available hardware.
"""

import os
import sys
import logging
import platform
import psutil
import torch
from pathlib import Path
from typing import Dict, Tuple, Optional, Union, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Default model path
DEFAULT_MODEL_DIR = os.path.join(os.path.expanduser("~"), ".cache", "r1-1776")

def get_system_info() -> Dict[str, Any]:
    """
    Get information about the system's hardware capabilities.
    
    Returns:
        Dict containing system information including CPU, RAM, and GPU details
    """
    system_info = {
        "os": platform.system(),
        "cpu_count": psutil.cpu_count(logical=False),
        "cpu_threads": psutil.cpu_count(logical=True),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "ram_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        "has_cuda": torch.cuda.is_available(),
        "has_mps": hasattr(torch.backends, "mps") and torch.backends.mps.is_available(),
        "gpu_count": 0,
        "gpu_info": [],
        "gpu_memory_gb": 0
    }
    
    # Get GPU information if available
    if system_info["has_cuda"]:
        system_info["gpu_count"] = torch.cuda.device_count()
        for i in range(system_info["gpu_count"]):
            gpu_name = torch.cuda.get_device_name(i)
            gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
            system_info["gpu_info"].append({
                "index": i,
                "name": gpu_name,
                "memory_gb": round(gpu_memory, 2)
            })
            system_info["gpu_memory_gb"] += gpu_memory
        system_info["gpu_memory_gb"] = round(system_info["gpu_memory_gb"], 2)
    elif system_info["has_mps"]:  # Apple Silicon
        system_info["gpu_count"] = 1
        system_info["gpu_info"].append({
            "index": 0,
            "name": "Apple Silicon",
            "memory_gb": "shared"  # Apple Silicon uses shared memory
        })
    
    return system_info

def determine_optimal_config(system_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine the optimal configuration for loading the model based on system capabilities.
    
    Args:
        system_info: Dictionary containing system hardware information
        
    Returns:
        Dictionary with optimal configuration parameters
    """
    config = {
        "device_map": "auto",
        "torch_dtype": torch.float16,
        "load_in_8bit": False,
        "load_in_4bit": False,
        "use_cpu": False,
        "offload_folder": None,
        "max_memory": None,
        "low_cpu_mem_usage": True,
    }
    
    # High-end GPU with plenty of VRAM (>= 24GB)
    if system_info["has_cuda"] and system_info["gpu_memory_gb"] >= 24:
        logger.info("High-end GPU detected with ≥24GB VRAM. Using full precision FP16.")
        # Already set to optimal defaults
    
    # Mid-range GPU (12-24GB VRAM)
    elif system_info["has_cuda"] and system_info["gpu_memory_gb"] >= 12:
        logger.info("Mid-range GPU detected with 12-24GB VRAM. Using FP16 with optimized memory usage.")
        # Already set to optimal defaults
    
    # Low-end GPU (8-12GB VRAM)
    elif system_info["has_cuda"] and system_info["gpu_memory_gb"] >= 8:
        logger.info("Low-end GPU detected with 8-12GB VRAM. Using 8-bit quantization.")
        config["load_in_8bit"] = True
    
    # Very low-end GPU (4-8GB VRAM)
    elif system_info["has_cuda"] and system_info["gpu_memory_gb"] >= 4:
        logger.info("Very low-end GPU detected with 4-8GB VRAM. Using 4-bit quantization.")
        config["load_in_4bit"] = True
        config["bnb_4bit_compute_dtype"] = torch.float16
        config["bnb_4bit_quant_type"] = "nf4"
    
    # Apple Silicon (M1/M2/M3)
    elif system_info["has_mps"]:
        logger.info("Apple Silicon detected. Using MPS device with 4-bit quantization.")
        config["device_map"] = "mps"
        config["load_in_4bit"] = True
        config["bnb_4bit_compute_dtype"] = torch.float16
        config["bnb_4bit_quant_type"] = "nf4"
    
    # CPU only with good amount of RAM (>= 16GB)
    elif system_info["ram_total_gb"] >= 16:
        logger.info("No GPU detected, but sufficient RAM. Using CPU with 4-bit quantization.")
        config["device_map"] = "cpu"
        config["load_in_4bit"] = True
        config["bnb_4bit_compute_dtype"] = torch.float16
        config["bnb_4bit_quant_type"] = "nf4"
        config["use_cpu"] = True
    
    # Low RAM system (< 16GB)
    else:
        logger.warning("Low-resource system detected. Performance may be severely limited.")
        logger.info("Using CPU with 4-bit quantization and disk offloading.")
        config["device_map"] = "cpu"
        config["load_in_4bit"] = True
        config["bnb_4bit_compute_dtype"] = torch.float16
        config["bnb_4bit_quant_type"] = "nf4"
        config["use_cpu"] = True
        config["offload_folder"] = os.path.join(os.path.expanduser("~"), ".cache", "r1-1776-offload")
        os.makedirs(config["offload_folder"], exist_ok=True)
    
    # For multi-GPU setups, optimize memory allocation across GPUs
    if system_info["has_cuda"] and system_info["gpu_count"] > 1:
        logger.info(f"Multi-GPU setup detected with {system_info['gpu_count']} GPUs. Optimizing memory allocation.")
        max_memory = {}
        for i in range(system_info["gpu_count"]):
            # Allocate 90% of available memory to each GPU
            max_memory[i] = f"{int(system_info['gpu_info'][i]['memory_gb'] * 0.9)}GiB"
        # Reserve some CPU RAM as well
        max_memory["cpu"] = f"{int(system_info['ram_available_gb'] * 0.5)}GiB"
        config["max_memory"] = max_memory
    
    return config

def load_model(
    model_dir: str = DEFAULT_MODEL_DIR,
    force_config: Optional[Dict[str, Any]] = None,
    verbose: bool = False
) -> Tuple[Any, Any]:
    """
    Load the R1-1776 model with optimal configuration for the current hardware.
    
    Args:
        model_dir: Directory where the model is saved
        force_config: Optional configuration to override automatic detection
        verbose: Whether to print detailed information
    
    Returns:
        Tuple of (tokenizer, model)
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if model directory exists
    if not os.path.exists(model_dir):
        raise FileNotFoundError(
            f"Model directory '{model_dir}' not found. "
            f"Please run the setup script first: python run_r1_1776_launcher.py"
        )
    
    try:
        # Import here to ensure dependencies are installed
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import bitsandbytes as bnb
        
        # Get system information
        logger.info("Analyzing system hardware...")
        system_info = get_system_info()
        
        if verbose:
            logger.debug("System information:")
            for key, value in system_info.items():
                if key != "gpu_info":  # Skip detailed GPU info in the summary
                    logger.debug(f"  {key}: {value}")
            if system_info["gpu_info"]:
                logger.debug("  GPU details:")
                for gpu in system_info["gpu_info"]:
                    logger.debug(f"    {gpu['name']} ({gpu['memory_gb']} GB)")
        
        # Determine optimal configuration
        config = force_config if force_config else determine_optimal_config(system_info)
        
        if verbose:
            logger.debug("Loading configuration:")
            for key, value in config.items():
                logger.debug(f"  {key}: {value}")
        
        # Load tokenizer
        logger.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        
        # Load model with optimal configuration
        logger.info("Loading model with optimal configuration for your hardware...")
        
        # Extract quantization and device settings
        load_kwargs = {k: v for k, v in config.items() if k not in ["use_cpu", "offload_folder"]}
        
        # Load the model
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            **load_kwargs
        )
        
        logger.info("Model loaded successfully!")
        
        # Print memory usage if verbose
        if verbose and torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                allocated = torch.cuda.memory_allocated(i) / (1024**3)
                reserved = torch.cuda.memory_reserved(i) / (1024**3)
                logger.debug(f"GPU {i} memory: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved")
        
        return tokenizer, model
        
    except ImportError as e:
        logger.error(f"Missing required dependencies: {e}")
        logger.info("Please install the required packages:")
        logger.info("  pip install transformers torch accelerate bitsandbytes")
        raise
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise

def generate_text(
    tokenizer: Any,
    model: Any,
    prompt: str,
    max_new_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9,
    repetition_penalty: float = 1.1,
    do_sample: bool = True
) -> str:
    """
    Generate text using the loaded model.
    
    Args:
        tokenizer: The model tokenizer
        model: The loaded model
        prompt: Input text to generate from
        max_new_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature (higher = more random)
        top_p: Nucleus sampling parameter
        repetition_penalty: Penalty for repeating tokens
        do_sample: Whether to use sampling (vs greedy decoding)
    
    Returns:
        Generated text
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            inputs["input_ids"],
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            do_sample=do_sample
        )
    
    # Decode and extract just the generated part
    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    generated_text = full_text[len(prompt):]
    
    return generated_text.strip()

if __name__ == "__main__":
    # If run directly, print system information
    print("R1-1776 Model Utilities")
    print("=" * 50)
    print("System Information:")
    
    system_info = get_system_info()
    for key, value in system_info.items():
        if key != "gpu_info":  # Skip detailed GPU info in the summary
            print(f"  {key}: {value}")
    
    if system_info["gpu_info"]:
        print("  GPU details:")
        for gpu in system_info["gpu_info"]:
            print(f"    {gpu['name']} ({gpu['memory_gb']} GB)")
    
    print("\nRecommended Configuration:")
    config = determine_optimal_config(system_info)
    for key, value in config.items():
        print(f"  {key}: {value}")