# Selenium Qt Browser

A Python application that provides a PyQt6-based web browser with multiple tabs for web browsing, AI chat, and terminal access, along with direct programmatic control for automation.

## Features

- Built-in web browser using PyQt6 and QWebEngineView
- Multiple tab types:
  - Web Browser tabs for standard web browsing
  - AI Chat tabs for communicating with two AI assistants
  - Terminal tabs for command-line access
- Direct programmatic control for automation
- Command-line interface for interactive control
- Persistent cookies, cache, and session data across restarts
- Integration with AI models (R1-1776 and DeepSeek)

## Transferring to a New Machine

### Prerequisites

- Python 3.8 or higher
- Chrome, Firefox, or Edge browser installed
- Git (for cloning the repository)

### Option 1: Quick Setup (Recommended)

1. Clone this repository:
   ```
   git clone https://github.com/lanilsson/DeepseekP2.2.git
   cd DeepseekP2.2
   ```

2. Run the setup script:
   - On macOS/Linux:
     ```
     chmod +x setup.sh
     ./setup.sh
     ```
   - On Windows:
     ```
     setup.bat
     ```

3. Activate the virtual environment:
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```
   - On Windows:
     ```
     venv\Scripts\activate
     ```

4. Run the application:
   ```
   python run.py
   ```

### Option 2: Manual Setup

1. Clone this repository:
   ```
   git clone https://github.com/lanilsson/DeepseekP2.2.git
   cd DeepseekP2.2
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create necessary directories:
   ```
   mkdir -p DeepSeek_Models/models
   mkdir -p DeepSeek_Models/history
   mkdir -p DeepSeek_Models/workspace
   ```

6. Install the DeepSeek_Models package:
   ```
   pip install -e DeepSeek_Models
   ```

## Usage

### Running the Browser

1. Run the application:
   ```
   python run.py
   ```

2. Command-line options:
   ```
   python run.py --help
   ```
   
   Available options:
   - `--url URL`: URL to open on startup
   - `--profile PROFILE`: Browser profile to use
   - `--headless`: Run in headless mode

### Using the Browser Interface

The browser interface provides three types of tabs:

1. **Web Browser Tab**:
   - Use the address bar to navigate to websites
   - Use the navigation buttons (back, forward, refresh, home)
   - Create new tabs using the "+" button

2. **AI Chat Tab**:
   - Communicate with two AI assistants
   - Select which AI to send messages to
   - View conversation history

3. **Terminal Tab**:
   - Execute shell commands
   - View command output
   - Access the file system

### Using Direct Programmatic Control

The browser includes a controller that allows direct programmatic control of the browser, terminal, and chat functionality.

1. Start the browser:
   ```
   python run.py
   ```

2. Use the controller to control the browser:
   ```python
   from selenium_qt_browser.controller import get_controller
   
   controller = get_controller()
   
   # Get information about the current page
   page_info = controller.get_page_info()
   
   # Navigate to a URL
   controller.navigate("https://example.com")
   
   # Click an element
   controller.click_element(selector="a.button")
   
   # Fill a form field
   controller.fill_input("Hello, world!", selector="#input-field")
   
   # Execute a terminal command
   result = controller.execute_terminal_command("ls -la")
   
   # Send a message to the AI chat
   controller.send_chat_message("What's the weather like today?")
   ```

3. Available controller methods:
   - `get_tabs_info()` - Get information about all tabs
   - `switch_to_tab(tab_index)` - Switch to a specific tab
   - `create_tab(tab_type)` - Create a new tab
   - `close_tab(tab_index)` - Close a specific tab
   - `get_page_info()` - Get information about the current webpage
   - `navigate(url)` - Navigate to a URL
   - `click_element(element_id, selector, position)` - Click an element on the webpage
   - `fill_input(text, element_id, selector)` - Fill a text input field
   - `go_back()` - Navigate back in history
   - `go_forward()` - Navigate forward in history
   - `refresh()` - Refresh the current page
   - `execute_terminal_command(command)` - Execute a command in the terminal
   - `get_current_directory()` - Get the current working directory
   - `send_chat_message(message, ai)` - Send a message to the AI chat

### Using the Command-Line Interface

The browser includes a command-line interface for interactive control:

1. Start the browser:
   ```
   python run.py
   ```

2. Run the direct CLI client:
   ```
   python examples/direct_cli.py
   ```

3. Available commands:
   - `status` - Get the server status
   - `tabs` - List all tabs
   - `switch <tab_index>` - Switch to a specific tab
   - `create <tab_type>` - Create a new tab (browser, chat, terminal)
   - `close <tab_index>` - Close a specific tab
   - `info` - Get information about the current webpage
   - `navigate <url>` - Navigate to a URL
   - `click <selector>` - Click an element on the webpage
   - `fill <selector> <text>` - Fill a text input field
   - `back` - Navigate back in history
   - `forward` - Navigate forward in history
   - `refresh` - Refresh the current page
   - `elements` - List all interactive elements on the current page
   - `terminal <command>` - Execute a command in the terminal
   - `pwd` - Get the current working directory of the terminal
   - `chat <message>` - Send a message to the AI chat
   - `exit` or `quit` - Exit the CLI

## AI Models

### R1-1776 Model

This project includes scripts to download and set up the R1-1776 model from Hugging Face for local inference.

#### Setting up the R1-1776 Model

1. Run the setup script:
   ```
   python run_r1_1776_launcher.py
   ```

2. Command-line options:
   ```
   python run_r1_1776_launcher.py --help
   ```
   
   Available options:
   - `--model-dir PATH`: Directory to save the model (default: ~/.cache/r1-1776)
   - `--use-8bit`: Load model in 8-bit quantization for reduced memory usage
   - `--use-4bit`: Load model in 4-bit quantization for minimal memory usage
   - `--skip-test`: Skip testing the model after download

3. Using the model in your Python code:
   ```python
   import torch
   from transformers import AutoTokenizer, AutoModelForCausalLM
   
   # Load the model (adjust path if you used a custom model directory)
   model_path = "~/.cache/r1-1776"  # or your custom path
   
   tokenizer = AutoTokenizer.from_pretrained(model_path)
   model = AutoModelForCausalLM.from_pretrained(
       model_path,
       torch_dtype=torch.float16,
       device_map="auto"
   )
   
   # Generate text
   prompt = "Hello, I'm interested in learning about artificial intelligence."
   inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
   
   with torch.no_grad():
       outputs = model.generate(
           inputs["input_ids"],
           max_new_tokens=100,
           temperature=0.7,
           do_sample=True
       )
   
   response = tokenizer.decode(outputs[0], skip_special_tokens=True)
   print(response)
   ```

### Deepseek Dual Models

The project also includes support for running Deepseek Dual Models:

```
python run_deepseek.py
```

## Configuration

The application stores its configuration in a `config.json` file in the user's home directory. This includes:

- Browser settings
- Default homepage
- User preferences

## Project Structure

```
DeepseekP2.2/
├── selenium_qt_browser/     # Main browser application
├── DeepSeek_Models/         # DeepSeek model integration
│   ├── models/              # Directory for model files
│   ├── history/             # Directory for chat history
│   └── workspace/           # Directory for workspace files
├── examples/                # Example scripts
├── run.py                   # Main entry point
├── run_r1_1776.py           # R1-1776 model runner
├── run_r1_1776_launcher.py  # R1-1776 model launcher
├── run_deepseek.py          # DeepSeek models runner
├── requirements.txt         # Python dependencies
├── setup.sh                 # Setup script for macOS/Linux
├── setup.bat                # Setup script for Windows
├── create_archive.sh        # Archive creation script for macOS/Linux
├── create_archive.bat       # Archive creation script for Windows
├── push_to_github.sh        # GitHub push script for macOS/Linux
├── push_to_github.bat       # GitHub push script for Windows
├── SETUP_COMMANDS.md        # Detailed setup commands
└── README.md                # This file
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.