#!/usr/bin/env python3
"""
DeepSeek-R1-Distill-Qwen-32B Model CLI

This script provides a command-line interface for interacting with the DeepSeek-R1-Distill-Qwen-32B model.
"""

import os
import sys
import argparse
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

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='DeepSeek-R1-Distill-Qwen-32B Model CLI',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Model location options
    model_group = parser.add_argument_group('Model Location')
    model_group.add_argument('--model-dir', type=str,
                        default=os.path.join(os.path.expanduser("~"), ".cache", "deepseek-r1-distill-qwen-32b"),
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
    gen_group.add_argument('--max-tokens', type=int, default=512,
                        help='Maximum number of tokens to generate')
    gen_group.add_argument('--temperature', type=float, default=0.7,
                        help='Sampling temperature (higher = more random)')
    gen_group.add_argument('--top-p', type=float, default=0.9,
                        help='Nucleus sampling parameter')
    gen_group.add_argument('--repetition-penalty', type=float, default=1.1,
                        help='Penalty for repeating tokens')
    gen_group.add_argument('--system-prompt', type=str,
                        default="You are DeepSeek, an AI assistant based on the DeepSeek-R1-Distill-Qwen-32B model. You are helpful, harmless, and honest.",
                        help='System prompt to control the model behavior')
    
    # Other options
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed information about hardware and configuration')
    parser.add_argument('--non-interactive', action='store_true',
                        help='Run in non-interactive mode (requires --prompt)')
    parser.add_argument('--prompt', type=str,
                        help='Prompt to use in non-interactive mode')
    
    return parser.parse_args()

def interactive_mode(session, args):
    """Run the CLI in interactive mode."""
    print("\nDeepSeek-R1-Distill-Qwen-32B Model CLI - Interactive Mode")
    print("Type 'exit', 'quit', or Ctrl+C to exit")
    print("Type 'clear' to clear the conversation history")
    print("Type 'help' for help")
    print("-" * 50)
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Check for special commands
            if user_input.lower() in ['exit', 'quit']:
                print("Exiting...")
                break
            elif user_input.lower() == 'clear':
                session.history = []
                session._save_history()
                print("Conversation history cleared")
                continue
            elif user_input.lower() == 'help':
                print("\nCommands:")
                print("  exit, quit - Exit the program")
                print("  clear - Clear the conversation history")
                print("  help - Show this help message")
                continue
            elif not user_input:
                continue
            
            # Generate response
            print("\nGenerating response...")
            response = session.generate_response(
                prompt=user_input,
                max_new_tokens=args.max_tokens,
                temperature=args.temperature,
                top_p=args.top_p,
                repetition_penalty=args.repetition_penalty,
                system_prompt=args.system_prompt
            )
            
            # Print the response
            print(f"\nAI: {response}")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error: {e}")

def non_interactive_mode(session, args):
    """Run the CLI in non-interactive mode."""
    if not args.prompt:
        logger.error("Non-interactive mode requires a prompt (--prompt)")
        return
    
    try:
        # Generate response
        logger.info(f"Generating response to: '{args.prompt}'")
        response = session.generate_response(
            prompt=args.prompt,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            repetition_penalty=args.repetition_penalty,
            system_prompt=args.system_prompt
        )
        
        # Print the response
        print(response)
        
    except Exception as e:
        logger.error(f"Error: {e}")

def main():
    """Main function to run the CLI."""
    args = parse_arguments()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create force_config based on arguments
    force_config = None
    if args.use_8bit or args.use_4bit or args.force_cpu:
        import torch
        force_config = {}
        if args.use_8bit:
            force_config["load_in_8bit"] = True
        elif args.use_4bit:
            force_config["load_in_4bit"] = True
            force_config["bnb_4bit_compute_dtype"] = torch.float16
            force_config["bnb_4bit_quant_type"] = "nf4"
        if args.force_cpu:
            force_config["device_map"] = "cpu"
    
    try:
        # Create a new session
        logger.info("Creating a new model session")
        session = ModelSession(args.model_dir, args.session_id)
        
        # Load the model
        logger.info("Loading the model (this may take a moment)...")
        session.load_model(force_config=force_config, verbose=args.verbose)
        
        # Run in interactive or non-interactive mode
        if args.non_interactive:
            non_interactive_mode(session, args)
        else:
            interactive_mode(session, args)
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Always unload the model to free up memory
        logger.info("Unloading model...")
        try:
            session.unload_model()
        except:
            pass
        logger.info("Done")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)