#!/bin/bash
# Setup script for Selenium Qt Browser with AI Models
# This script will set up the application on a new machine

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Selenium Qt Browser with AI Models Setup${NC}"
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

# Create virtual environment
echo -e "${GREEN}Creating virtual environment...${NC}"
python3 -m venv venv || {
    echo -e "${RED}Failed to create virtual environment.${NC}"
    exit 1
}

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate || {
    echo -e "${RED}Failed to activate virtual environment.${NC}"
    exit 1
}

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -r requirements.txt || {
    echo -e "${RED}Failed to install dependencies.${NC}"
    exit 1
}

# Create necessary directories
echo -e "${GREEN}Creating necessary directories...${NC}"
mkdir -p DeepSeek_Models/models
mkdir -p DeepSeek_Models/history
mkdir -p DeepSeek_Models/workspace

# Install DeepSeek_Models package
echo -e "${GREEN}Installing DeepSeek_Models package...${NC}"
pip install -e DeepSeek_Models || {
    echo -e "${RED}Failed to install DeepSeek_Models package.${NC}"
    exit 1
}

echo -e "${GREEN}Setup completed successfully!${NC}"
echo ""
echo "To use the application:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run the browser:"
echo "   python run.py"
echo ""
echo "3. To set up the R1-1776 model (optional):"
echo "   python run_r1_1776_launcher.py"
echo ""
echo "4. To run the DeepSeek models (optional):"
echo "   python run_deepseek.py"
echo ""
echo "For more information, see the README.md file."