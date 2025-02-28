# DeepSeek_Models - DeepSeek-R1-Distill-Qwen-32B Model Launcher

This package provides a simple interface for loading and interacting with the DeepSeek-R1-Distill-Qwen-32B model. It handles model loading, memory management, and conversation history.

## Features

- Smart model loading with hardware detection
- Memory management for efficient operation
- Conversation history tracking and persistence
- Simple API for generating responses

## Directory Structure

```
DeepSeek_Models/
├── start.py         # Main module with ModelSession class
├── example.py       # Example usage script
├── history/         # Stores conversation history files
└── workspace/       # Workspace for model files and outputs
```

## Usage

### Basic Usage

```python
from DeepSeek_Models import ModelSession

# Create a session with the model
session = ModelSession('/path/to/model')

# Load the model
session.load_model()

# Generate a response
response = session.generate_response('Your prompt here')
print(response)

# Unload the model when done
session.unload_model()
```

### Command Line Usage

You can also run the `start.py` script directly:

```bash
python DeepSeek_Models/start.py --model-dir /path/to/model
```

Run the example script:

```bash
python DeepSeek_Models/example.py
```

### Interactive CLI

The package includes an interactive CLI for chatting with the model:

```bash
python DeepSeek_Models/cli.py
```

This opens an interactive chat session where you can type prompts and get responses.

You can also use it in non-interactive mode:

```bash
python DeepSeek_Models/cli.py --prompt "Your prompt here" --non-interactive
```

### Options

The `ModelSession` class and command line interface support several options:

- `model_dir`: Directory where the model is saved
- `session_id`: Session ID for loading/saving history
- `force_config`: Configuration to override automatic hardware detection
- `verbose`: Whether to print detailed information
- `system_prompt`: System prompt to control the model's behavior

### Hardware Optimization

The module automatically detects your hardware capabilities and configures the model for optimal performance. You can override this with the following options:

- `--use-8bit`: Load model in 8-bit quantization for reduced memory usage
- `--use-4bit`: Load model in 4-bit quantization for minimal memory usage
- `--force-cpu`: Force CPU usage even if GPU is available

## API Reference

### ModelSession

```python
class ModelSession:
    def __init__(self, model_dir: str, session_id: Optional[str] = None):
        """
        Initialize a model session.
        
        Args:
            model_dir: Directory where the model is saved
            session_id: Optional session ID for loading/saving history
        """
        
    def load_model(self, force_config: Optional[Dict[str, Any]] = None, verbose: bool = False):
        """
        Load the model with optimal configuration.
        
        Args:
            force_config: Optional configuration to override automatic detection
            verbose: Whether to print detailed information
        """
        
    def unload_model(self):
        """Unload the model to free up memory."""
        
    def add_to_history(self, role: str, content: str):
        """
        Add a message to the conversation history.
        
        Args:
            role: The role of the message sender ('user' or 'assistant')
            content: The message content
        """
        
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
```

## Requirements

- Python 3.8+
- PyTorch
- Transformers
- Accelerate
- Bitsandbytes (for quantization)
- Sentencepiece
- Protobuf
- Psutil (for hardware detection)

## License

This project is licensed under the MIT License - see the LICENSE file for details.