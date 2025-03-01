#!/bin/bash
# Script to install system dependencies required for Selenium Qt Browser

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing system dependencies for Selenium Qt Browser${NC}"
echo "=============================================="

# Check if we're running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}This script needs to install system packages and may require sudo privileges.${NC}"
    echo "You may be prompted for your password."
fi

# Detect the Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    echo -e "${RED}Could not detect Linux distribution.${NC}"
    DISTRO="unknown"
fi

echo "Detected Linux distribution: $DISTRO"

# Install dependencies based on the distribution
case $DISTRO in
    ubuntu|debian|pop|mint|elementary)
        echo "Installing dependencies for Ubuntu/Debian-based systems..."
        sudo apt-get update
        sudo apt-get install -y \
            libgl1-mesa-glx \
            libegl1-mesa \
            libxkbcommon-x11-0 \
            libxcb-icccm4 \
            libxcb-image0 \
            libxcb-keysyms1 \
            libxcb-randr0 \
            libxcb-render-util0 \
            libxcb-xinerama0 \
            libxcb-xkb1 \
            libxkbcommon-x11-0 \
            libfontconfig1 \
            libdbus-1-3
        ;;
    fedora|rhel|centos)
        echo "Installing dependencies for Fedora/RHEL-based systems..."
        sudo dnf install -y \
            mesa-libGL \
            mesa-libEGL \
            libxkbcommon-x11 \
            libXcomposite \
            libXcursor \
            libXi \
            libXtst \
            libXrandr \
            libXScrnSaver \
            alsa-lib \
            fontconfig
        ;;
    arch|manjaro)
        echo "Installing dependencies for Arch-based systems..."
        sudo pacman -Sy --noconfirm \
            mesa \
            libxkbcommon-x11 \
            libxcb \
            xcb-util-image \
            xcb-util-keysyms \
            xcb-util-renderutil \
            xcb-util-wm
        ;;
    *)
        echo -e "${RED}Unsupported Linux distribution: $DISTRO${NC}"
        echo "Please install the following packages manually:"
        echo "- OpenGL libraries (libGL.so.1)"
        echo "- X11 libraries"
        echo "- XCB libraries"
        echo "- FontConfig"
        exit 1
        ;;
esac

echo -e "${GREEN}System dependencies installed successfully!${NC}"
echo "You can now run the application with: python run.py"