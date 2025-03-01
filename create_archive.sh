#!/bin/bash
# Script to create a zip archive of the project for transfer to a new machine

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Creating archive of Selenium Qt Browser for transfer${NC}"
echo "=============================================="

# Get the current directory name
DIR_NAME=$(basename "$(pwd)")

# Create a temporary directory for the files to include
TEMP_DIR="temp_archive"
mkdir -p "$TEMP_DIR"

# Copy necessary files and directories
echo "Copying files..."

# Main application files
cp -r selenium_qt_browser "$TEMP_DIR/"
cp -r examples "$TEMP_DIR/"

# DeepSeek Models (excluding large files)
mkdir -p "$TEMP_DIR/DeepSeek_Models"
cp DeepSeek_Models/*.py "$TEMP_DIR/DeepSeek_Models/"
cp DeepSeek_Models/README.md "$TEMP_DIR/DeepSeek_Models/"
cp DeepSeek_Models/install.sh "$TEMP_DIR/DeepSeek_Models/"
cp DeepSeek_Models/setup.py "$TEMP_DIR/DeepSeek_Models/"
mkdir -p "$TEMP_DIR/DeepSeek_Models/models"
mkdir -p "$TEMP_DIR/DeepSeek_Models/history"
mkdir -p "$TEMP_DIR/DeepSeek_Models/workspace"

# Configuration and setup files
cp requirements.txt "$TEMP_DIR/"
cp setup.sh "$TEMP_DIR/"
cp setup.bat "$TEMP_DIR/"
cp README.md "$TEMP_DIR/"
cp LICENSE "$TEMP_DIR/"
cp .gitignore "$TEMP_DIR/"

# Runner scripts
cp run.py "$TEMP_DIR/"
cp run_r1_1776.py "$TEMP_DIR/"
cp run_r1_1776_launcher.py "$TEMP_DIR/"
cp run_deepseek.py "$TEMP_DIR/"
cp r1_1776_utils.py "$TEMP_DIR/"
cp create_archive.sh "$TEMP_DIR/"

# Create the zip archive
echo "Creating zip archive..."
zip -r "${DIR_NAME}_transfer.zip" "$TEMP_DIR"

# Rename the zip to remove the temp directory name
mv "${DIR_NAME}_transfer.zip" "selenium_qt_browser_transfer.zip"

# Clean up
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

echo -e "${GREEN}Archive created: selenium_qt_browser_transfer.zip${NC}"
echo "Transfer this file to your new machine and extract it to use the application."
echo "After extracting, run setup.sh (Linux/macOS) or setup.bat (Windows) to set up the application."