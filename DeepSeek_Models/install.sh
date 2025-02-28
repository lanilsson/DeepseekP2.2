#!/bin/bash
# Installation script for DeepSeek_Models

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}DeepSeek-R1-Distill-Qwen-32B Installation Script${NC}"
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
    echo -e "${RED}Error: Python 3.8 or higher is required.${NC}"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo -e "${GREEN}Python version $PYTHON_VERSION detected.${NC}"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}Warning: pip3 is not installed.${NC}"
    echo "Attempting to install pip..."
    python3 -m ensurepip --upgrade || {
        echo -e "${RED}Failed to install pip.${NC}"
        echo "Please install pip manually and try again."
        exit 1
    }
fi

# Install the package
echo "Installing DeepSeek_Models..."
cd "$(dirname "$0")/.." || {
    echo -e "${RED}Failed to navigate to the package directory.${NC}"
    exit 1
}

# Install in development mode
pip3 install -e DeepSeek_Models || {
    echo -e "${RED}Failed to install DeepSeek_Models.${NC}"
    exit 1
}

echo -e "${GREEN}Installation successful!${NC}"
echo ""
echo "You can now use DeepSeek_Models in your Python code:"
echo "  from DeepSeek_Models import ModelSession"
echo ""
echo "Or use the command-line interface:"
echo "  deepseek-model"
echo ""
echo "For more information, see the README.md file."