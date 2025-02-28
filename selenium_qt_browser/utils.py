"""
Utils Module - Utility functions for the Selenium Qt Browser

This module contains utility functions for file operations, configuration
management, and other helper functions.
"""

import os
import json
import logging
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('selenium_qt_browser')

# Application constants
APP_NAME = "Selenium Qt Browser"
APP_VERSION = "1.0.0"
CONFIG_DIR = Path.home() / ".selenium_qt_browser"
CONFIG_FILE = CONFIG_DIR / "config.json"
PROFILES_DIR = CONFIG_DIR / "profiles"

# Default configuration
DEFAULT_CONFIG = {
    "general": {
        "default_profile": "default",
        "start_url": "https://www.google.com",
        "save_session": True,
        "clear_cache_on_exit": False
    },
    "browser": {
        "user_agent": "",  # Empty string means use default
        "javascript_enabled": True,
        "cookies_enabled": True,
        "plugins_enabled": True,
        "developer_extras_enabled": True
    },
    "ui": {
        "theme": "system",  # system, light, dark
        "font_family": "",  # Empty string means use system default
        "font_size": 10,
        "show_status_bar": True,
        "show_bookmarks_bar": True
    }
}


def ensure_app_directories() -> None:
    """Ensure all application directories exist."""
    CONFIG_DIR.mkdir(exist_ok=True)
    PROFILES_DIR.mkdir(exist_ok=True)
    
    logger.info(f"Application directories created at {CONFIG_DIR}")


def load_config() -> Dict[str, Any]:
    """Load the application configuration from the config file."""
    ensure_app_directories()
    
    if not CONFIG_FILE.exists():
        # Create default config file if it doesn't exist
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # Merge with default config to ensure all keys exist
        merged_config = DEFAULT_CONFIG.copy()
        deep_update(merged_config, config)
        
        return merged_config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """Save the application configuration to the config file."""
    ensure_app_directories()
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info("Configuration saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False


def deep_update(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """Recursively update a nested dictionary with another nested dictionary."""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_update(target[key], value)
        else:
            target[key] = value


def get_system_info() -> Dict[str, str]:
    """Get system information."""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": platform.python_version(),
        "platform": platform.platform()
    }


def open_file_explorer(path: str) -> None:
    """Open the system file explorer at the specified path."""
    path = os.path.normpath(path)
    
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", path])
    else:  # Linux
        subprocess.run(["xdg-open", path])


def get_available_profiles() -> list:
    """Get a list of available browser profiles."""
    ensure_app_directories()
    
    profiles = []
    for item in PROFILES_DIR.iterdir():
        if item.is_dir():
            profiles.append(item.name)
    
    return profiles


def create_profile(profile_name: str) -> bool:
    """Create a new browser profile."""
    ensure_app_directories()
    
    profile_dir = PROFILES_DIR / profile_name
    if profile_dir.exists():
        logger.warning(f"Profile '{profile_name}' already exists")
        return False
    
    try:
        profile_dir.mkdir()
        logger.info(f"Created profile: {profile_name}")
        return True
    except Exception as e:
        logger.error(f"Error creating profile '{profile_name}': {e}")
        return False


def delete_profile(profile_name: str) -> bool:
    """Delete a browser profile."""
    if profile_name == "default":
        logger.warning("Cannot delete the default profile")
        return False
    
    profile_dir = PROFILES_DIR / profile_name
    if not profile_dir.exists():
        logger.warning(f"Profile '{profile_name}' does not exist")
        return False
    
    try:
        # Recursively delete the profile directory
        import shutil
        shutil.rmtree(profile_dir)
        logger.info(f"Deleted profile: {profile_name}")
        return True
    except Exception as e:
        logger.error(f"Error deleting profile '{profile_name}': {e}")
        return False


def clear_browser_cache(profile_name: Optional[str] = None) -> bool:
    """Clear the browser cache for the specified profile or all profiles."""
    ensure_app_directories()
    
    try:
        if profile_name:
            # Clear cache for a specific profile
            cache_dir = PROFILES_DIR / profile_name / "cache"
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir)
                cache_dir.mkdir()
                logger.info(f"Cleared cache for profile: {profile_name}")
        else:
            # Clear cache for all profiles
            for profile_dir in PROFILES_DIR.iterdir():
                if profile_dir.is_dir():
                    cache_dir = profile_dir / "cache"
                    if cache_dir.exists():
                        import shutil
                        shutil.rmtree(cache_dir)
                        cache_dir.mkdir()
            logger.info("Cleared cache for all profiles")
        
        return True
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return False


# Initialize application directories when module is imported
ensure_app_directories()