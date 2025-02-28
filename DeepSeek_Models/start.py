#!/usr/bin/env python3
"""
DeepSeek-R1-Distill-Qwen-32B Model Launcher

This script loads the DeepSeek-R1-Distill-Qwen-32B model from the models folder and provides
a simple interface for interacting with it. It manages the model's history
and memory for efficient operation.
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Import required packages directly
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Default paths
DEFAULT_MODEL_DIR = os.path.join(os.path.expanduser("~"), ".cache", "deepseek-r1-distill-qwen-32b")
HISTORY_DIR = os.path.join(os.path.dirname(__file__), "history")
WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")

class ModelSession:
    """Manages a session with the DeepSeek-R1-Distill-Qwen-32B model, including history and memory."""
    
    def __init__(self, model_dir: str, session_id: Optional[str] = None):
        """
        Initialize a model session.
        
        Args:
            model_dir: Directory where the model is saved
            session_id: Optional session ID for loading/saving history
        """
        self.model_dir = model_dir
        self.session_id = session_id or f"session_{int(time.time())}"
        self.history = []
        self.tokenizer = None
        self.model = None
        self.loaded = False
        
        # Create history and workspace directories if they don't exist
        os.makedirs(HISTORY_DIR, exist_ok=True)
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        
        # History file path
        self.history_file = os.path.join(HISTORY_DIR, f"{self.session_id}.json")
        
        # Load existing history if available
        self._load_history()
    
    def _load_history(self):
        """Load conversation history from file if it exists."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                logger.info(f"Loaded history from {self.history_file}")
            except Exception as e:
                logger.error(f"Error loading history: {e}")
                self.history = []
    
    def _save_history(self):
        """Save conversation history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved history to {self.history_file}")
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    def load_model(self, force_config: Optional[Dict[str, Any]] = None, verbose: bool = False):
        """
        Load the model with optimal configuration.
        
        Args:
            force_config: Optional configuration to override automatic detection
            verbose: Whether to print detailed information
        """
        if self.loaded:
            logger.info("Model already loaded")
            return
        
        logger.info(f"Loading model from {self.model_dir}")
        
        try:
            # Determine optimal configuration based on hardware
            config = self._determine_optimal_config()
            
            # Apply force_config if provided
            if force_config:
                config.update(force_config)
            
            if verbose:
                logger.info("Using configuration:")
                for key, value in config.items():
                    logger.info(f"  {key}: {value}")
            
            # Load tokenizer and model
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_dir,
                trust_remote_code=True
            )
            
            logger.info("Loading model...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_dir,
                trust_remote_code=True,
                **config
            )
            
            self.loaded = True
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def _determine_optimal_config(self) -> Dict[str, Any]:
        """
        Determine the optimal configuration for loading the model based on system capabilities.
        
        Returns:
            Dictionary with optimal configuration parameters
        """
        config = {
            "device_map": "auto",
            "torch_dtype": torch.float16,
            "low_cpu_mem_usage": True,
        }
        
        # Check for CUDA availability
        if torch.cuda.is_available():
            gpu_memory = 0
            for i in range(torch.cuda.device_count()):
                gpu_memory += torch.cuda.get_device_properties(i).total_memory / (1024**3)
            
            logger.info(f"Found {torch.cuda.device_count()} GPU(s) with {gpu_memory:.2f}GB total memory")
            
            # High-end GPU with plenty of VRAM (>= 48GB)
            if gpu_memory >= 48:
                logger.info("High-end GPU detected with ≥48GB VRAM. Using full precision FP16.")
                # Already set to optimal defaults
            
            # Mid-range GPU (24-48GB VRAM)
            elif gpu_memory >= 24:
                logger.info("Mid-range GPU detected with 24-48GB VRAM. Using FP16 with optimized memory usage.")
                # Already set to optimal defaults
            
            # Low-end GPU (12-24GB VRAM)
            elif gpu_memory >= 12:
                logger.info("Low-end GPU detected with 12-24GB VRAM. Using 8-bit quantization.")
                config["load_in_8bit"] = True
            
            # Very low-end GPU (< 12GB VRAM)
            else:
                logger.info("Very low-end GPU detected with <12GB VRAM. Using 4-bit quantization.")
                config["load_in_4bit"] = True
                config["bnb_4bit_compute_dtype"] = torch.float16
                config["bnb_4bit_quant_type"] = "nf4"
        
        # Apple Silicon (M1/M2/M3)
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            logger.info("Apple Silicon detected. Using MPS device with 4-bit quantization.")
            config["device_map"] = "mps"
            config["load_in_4bit"] = True
            config["bnb_4bit_compute_dtype"] = torch.float16
            config["bnb_4bit_quant_type"] = "nf4"
        
        # CPU only
        else:
            logger.info("No GPU detected. Using CPU with 4-bit quantization.")
            config["device_map"] = "cpu"
            config["load_in_4bit"] = True
            config["bnb_4bit_compute_dtype"] = torch.float16
            config["bnb_4bit_quant_type"] = "nf4"
        
        return config
    
    def unload_model(self):
        """Unload the model to free up memory."""
        if not self.loaded:
            logger.info("Model not loaded")
            return
        
        try:
            # Clear model and tokenizer
            self.model = None
            self.tokenizer = None
            
            # Run garbage collection
            import gc
            gc.collect()
            
            # Clear CUDA cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.loaded = False
            logger.info("Model unloaded successfully")
            
        except Exception as e:
            logger.error(f"Error unloading model: {e}")
            raise
    
    def add_to_history(self, role: str, content: str):
        """
        Add a message to the conversation history.
        
        Args:
            role: The role of the message sender ('user' or 'assistant')
            content: The message content
        """
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        self._save_history()
    
    def generate_response(self, prompt: str,
                         max_new_tokens: int = 512,
                         temperature: float = 0.7,
                         top_p: float = 0.9,
                         repetition_penalty: float = 1.1,
                         do_sample: bool = True,
                         system_prompt: str = None):
        """
        Generate a response to the given prompt.
        
        Args:
            prompt: The input prompt
            max_new_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling parameter
            repetition_penalty: Penalty for repeating tokens
            do_sample: Whether to use sampling (vs greedy decoding)
            system_prompt: Optional system prompt to control the model's behavior
            
        Returns:
            The generated response
        """
        if not self.loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Add user message to history
        self.add_to_history("user", prompt)
        
        try:
            # Format the prompt for DeepSeek model
            formatted_prompt = self._format_prompt(prompt, system_prompt)
            
            # Generate response
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs["input_ids"],
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    repetition_penalty=repetition_penalty,
                    do_sample=do_sample,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode the response
            full_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract just the assistant's response
            response = self._extract_response(full_text, formatted_prompt)
            
            # Add assistant message to history
            self.add_to_history("assistant", response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def _format_prompt(self, prompt: str, system_prompt: str = None) -> str:
        """
        Format the prompt for the DeepSeek model.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            Formatted prompt
        """
        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = "You are DeepSeek, an AI assistant. You are helpful, harmless, and honest."
        
        # Format according to DeepSeek's expected format
        formatted_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        formatted_prompt += f"<|im_start|>user\n{prompt}<|im_end|>\n"
        formatted_prompt += "<|im_start|>assistant\n"
        
        return formatted_prompt
    
    def _extract_response(self, full_text: str, formatted_prompt: str) -> str:
        """
        Extract the assistant's response from the full generated text.
        
        Args:
            full_text: The full text generated by the model
            formatted_prompt: The formatted prompt that was used
            
        Returns:
            The assistant's response
        """
        # Remove the prompt from the beginning
        if full_text.startswith(formatted_prompt):
            response = full_text[len(formatted_prompt):]
        else:
            # If the prompt is not at the beginning (shouldn't happen), return the full text
            response = full_text
        
        # Remove any trailing tokens
        if "<|im_end|>" in response:
            response = response.split("<|im_end|>")[0]
        
        return response.strip()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='DeepSeek-R1-Distill-Qwen-32B Model Launcher',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Model location options
    model_group = parser.add_argument_group('Model Location')
    model_group.add_argument('--model-dir', type=str, default=DEFAULT_MODEL_DIR,
                        help='Directory where the model is saved')
    
    # Session options
    session_group = parser.add_argument_group('Session Options')
    session_group.add_argument('--session-id', type=str, default=None,
                        help='Session ID for loading/saving history')
    
    # Hardware configuration options
    hw_group = parser.add_argument_group('Hardware Configuration')
    hw_group.add_argument('--use-8bit', action='store_true',
                        help='Load model in 8-bit quantization for reduced memory usage')
    hw_group.add_argument('--use-4bit', action='store_true',
                        help='Load model in 4-bit quantization for minimal memory usage')
    hw_group.add_argument('--force-cpu', action='store_true',
                        help='Force CPU usage even if GPU is available')
    
    # Generation options
    gen_group = parser.add_argument_group('Generation Options')
    gen_group.add_argument('--system-prompt', type=str, default=None,
                        help='System prompt to control the model behavior')
    
    # Other options
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed information about hardware and configuration')
    
    return parser.parse_args()

def main():
    """Main function to load and run the model."""
    args = parse_arguments()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting DeepSeek-R1-Distill-Qwen-32B model session")
    
    # Create force_config based on arguments
    force_config = None
    if args.use_8bit or args.use_4bit or args.force_cpu:
        force_config = {}
        if args.use_8bit:
            force_config["load_in_8bit"] = True
        elif args.use_4bit:
            force_config["load_in_4bit"] = True
            force_config["bnb_4bit_compute_dtype"] = torch.float16
            force_config["bnb_4bit_quant_type"] = "nf4"
        if args.force_cpu:
            force_config["device_map"] = "cpu"
    
    # Create model session
    session = ModelSession(args.model_dir, args.session_id)
    
    # Load model
    session.load_model(force_config=force_config, verbose=args.verbose)
    
    logger.info("Model loaded and ready for use")
    logger.info("You can now use this session in your code:")
    logger.info("\nExample usage:")
    logger.info("```python")
    logger.info("from DeepSeek_Models.start import ModelSession")
    logger.info("session = ModelSession('path/to/model')")
    logger.info("session.load_model()")
    logger.info("response = session.generate_response('Your prompt here')")
    logger.info("print(response)")
    logger.info("```")
    
    # Clean up
    session.unload_model()
    logger.info("Session ended")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)