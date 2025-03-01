#!/bin/bash
# Script to add all important files to the GitHub repository

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Adding all important files to the GitHub repository${NC}"
echo "=============================================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: Git is not installed.${NC}"
    echo "Please install Git and try again."
    exit 1
fi

# Initialize git repository if not already initialized
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
fi

# Add the remote repository
echo "Adding remote repository..."
git remote remove origin 2>/dev/null
git remote add origin https://github.com/lanilsson/DeepseekP2.2.git

# Explicitly add all important files
echo "Adding important files to git..."

# Main Python files
git add run.py
git add run_deepseek.py
git add run_r1_1776.py
git add run_r1_1776_launcher.py
git add r1_1776_utils.py
git add setup.py

# Configuration files
git add requirements.txt
git add .gitignore
git add LICENSE
git add README.md
git add SETUP_COMMANDS.md

# Setup and utility scripts
git add setup.sh
git add setup.bat
git add create_archive.sh
git add create_archive.bat
git add push_to_github.sh
git add push_to_github.bat
git add add_all_files.sh
git add add_all_files.bat
git add install_system_dependencies.sh

# DeepSeek_Models directory
git add DeepSeek_Models/*.py
git add DeepSeek_Models/README.md
git add DeepSeek_Models/install.sh
git add DeepSeek_Models/setup.py
git add DeepSeek_Models/models/.gitkeep
git add DeepSeek_Models/history/.gitkeep
git add DeepSeek_Models/workspace/.gitkeep

# Examples directory
git add examples/*.py

# Selenium Qt Browser directory
git add selenium_qt_browser/*.py

# Commit the changes
echo "Committing changes..."
git commit -m "Add all important files for transfer to new machine"

# Get the current branch name
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)
if [ -z "$BRANCH_NAME" ]; then
    BRANCH_NAME="main"  # Default to main if branch name can't be determined
fi

# Push to GitHub
echo "Pushing to GitHub using branch: $BRANCH_NAME"
git push -u origin "$BRANCH_NAME"

echo -e "${GREEN}Successfully pushed all important files to GitHub!${NC}"
echo "Repository URL: https://github.com/lanilsson/DeepseekP2.2.git"