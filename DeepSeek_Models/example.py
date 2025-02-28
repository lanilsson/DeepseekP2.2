#!/usr/bin/env python3
"""
DeepSeek-R1-Distill-Qwen-32B Model Example

This script demonstrates how to use the ModelSession class to interact with the DeepSeek-R1-Distill-Qwen-32B model.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Import the ModelSession class
from start import ModelSession

def main():
    """Main function to demonstrate model usage."""
    # Default model path - change this to your model location if needed
    model_dir = os.path.join(os.path.expanduser("~"), ".cache", "deepseek-r1-distill-qwen-32b")
    
    # Create a new session
    logger.info("Creating a new model session")
    session = ModelSession(model_dir)
    
    try:
        # Load the model
        logger.info("Loading the model (this may take a moment)...")
        session.load_model(verbose=True)
        
        # Example prompt
        prompt = "Hello, I'm interested in learning about artificial intelligence. Can you explain what it is?"
        
        # System prompt (optional)
        system_prompt = "You are DeepSeek, an AI assistant based on the DeepSeek-R1-Distill-Qwen-32B model. You are helpful, harmless, and honest."
        
        # Generate a response
        logger.info(f"Generating response to: '{prompt}'")
        response = session.generate_response(
            prompt=prompt,
            max_new_tokens=200,
            temperature=0.7,
            system_prompt=system_prompt
        )
        
        # Print the response
        print("\n" + "="*50)
        print("PROMPT:")
        print(prompt)
        print("\nRESPONSE:")
        print(response)
        print("="*50 + "\n")
        
        # Show history
        logger.info(f"Conversation history saved to: {session.history_file}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Always unload the model to free up memory
        logger.info("Unloading model...")
        session.unload_model()
        logger.info("Done")

if __name__ == "__main__":
    main()