# Setup Commands for Selenium Qt Browser

This document provides all the commands you need to set up the Selenium Qt Browser application on a new machine.

## Prerequisites

- Python 3.8 or higher
- Git (for cloning the repository)
- Chrome, Firefox, or Edge browser installed

## Option 1: Using the Setup Scripts (Recommended)

### On macOS/Linux:

```bash
# 1. Clone the repository (if you haven't already)
git clone https://github.com/lanilsson/DeepseekP2.2.git
cd DeepseekP2.2

# 2. Make the setup script executable
chmod +x setup.sh

# 3. Run the setup script
./setup.sh

# 4. Activate the virtual environment
source venv/bin/activate

# 5. Run the application
python run.py
```

### On Windows:

```batch
# 1. Clone the repository (if you haven't already)
git clone https://github.com/lanilsson/DeepseekP2.2.git
cd DeepseekP2.2

# 2. Run the setup script
setup.bat

# 3. Activate the virtual environment
venv\Scripts\activate

# 4. Run the application
python run.py
```

## Option 2: Manual Setup

### On macOS/Linux:

```bash
# 1. Clone the repository (if you haven't already)
git clone https://github.com/lanilsson/DeepseekP2.2.git
cd DeepseekP2.2

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate the virtual environment
source venv/bin/activate

# 4. Install the required dependencies
pip install -r requirements.txt

# 5. Create necessary directories
mkdir -p DeepSeek_Models/models
mkdir -p DeepSeek_Models/history
mkdir -p DeepSeek_Models/workspace

# 6. Install the DeepSeek_Models package
pip install -e DeepSeek_Models

# 7. Run the application
python run.py
```

### On Windows:

```batch
# 1. Clone the repository (if you haven't already)
git clone https://github.com/lanilsson/DeepseekP2.2.git
cd DeepseekP2.2

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
venv\Scripts\activate

# 4. Install the required dependencies
pip install -r requirements.txt

# 5. Create necessary directories
mkdir DeepSeek_Models\models
mkdir DeepSeek_Models\history
mkdir DeepSeek_Models\workspace

# 6. Install the DeepSeek_Models package
pip install -e DeepSeek_Models

# 7. Run the application
python run.py
```

## Setting Up AI Models (Optional)

### R1-1776 Model:

```bash
# Run the R1-1776 model setup script
python run_r1_1776_launcher.py

# Options:
# --model-dir PATH: Directory to save the model (default: ~/.cache/r1-1776)
# --use-8bit: Load model in 8-bit quantization for reduced memory usage
# --use-4bit: Load model in 4-bit quantization for minimal memory usage
# --skip-test: Skip testing the model after download
```

### DeepSeek Models:

```bash
# Run the DeepSeek models
python run_deepseek.py
```

## Creating an Archive for Transfer

If you want to create an archive of the project for transfer to a new machine:

### On macOS/Linux:

```bash
# Make the script executable
chmod +x create_archive.sh

# Run the script
./create_archive.sh
```

### On Windows:

```batch
# Run the script
create_archive.bat
```

This will create a file called `selenium_qt_browser_transfer.zip` that you can transfer to the new machine.

## Pushing to GitHub

If you want to push the project to GitHub:

### On macOS/Linux:

```bash
# Make the script executable
chmod +x push_to_github.sh

# Run the script
./push_to_github.sh
```

### On Windows:

```batch
# Run the script
push_to_github.bat
```

This will push the project to the GitHub repository at https://github.com/lanilsson/DeepseekP2.2.git.