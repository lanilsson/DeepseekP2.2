#!/bin/bash
# Script to push the prepared files to GitHub

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Pushing Selenium Qt Browser to GitHub${NC}"
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

# Add all files
echo "Adding files to git..."
git add .

# Commit the changes
echo "Committing changes..."
git commit -m "Prepare app for transfer to new machine"

# Push to GitHub
echo "Pushing to GitHub..."
git push -u origin master

echo -e "${GREEN}Successfully pushed to GitHub!${NC}"
echo "Repository URL: https://github.com/lanilsson/DeepseekP2.2.git"