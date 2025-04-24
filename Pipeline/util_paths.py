import os
import sys
import json
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def resource_path(relative_path):
    """
    Get absolute path to resource, compatible with PyInstaller .exe
    """
    try:
        base_path = sys._MEIPASS  # Set by PyInstaller
    except AttributeError:        # If thats not there defalt to devpath
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


import platform
from pathlib import Path

def get_persistent_data_path(filename):
    """
    Returns a writable data path for your app:
    - Windows: %LOCALAPPDATA%\AutoConnect\data\
    - Linux/macOS/AppImage: ~/.autoconnect/data/
    """
    if platform.system() == "Windows":
        base_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base_dir = Path.home() / ".autoconnect"

    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / filename)


#used for verifiyng if a dir exists
# and creating it if it doesn't
def ensure_dir(path):
    full_path = get_persistent_data_path(path)
    os.makedirs(full_path, exist_ok=True)
    return full_path



def load_config():
    # Persistent user-writable config location
    persistent_path = get_persistent_data_path("config.json")

    # If user config exists → use that
    if os.path.exists(persistent_path):
        with open(persistent_path, "r") as f:
            return json.load(f)

    #If not → copy bundled default (either frozen or dev) to the persistent location
    if getattr(sys, "frozen", False):
        # If running frozen (AppImage / PyInstaller)
        default_path = os.path.join(sys._MEIPASS, "config.json")
    else:
        # Otherwise, use project root config.json
        default_path = resource_path("config.json")

    # Copy default to persistent location
    with open(default_path, "r") as src, open(persistent_path, "w") as dst:
        config_data = json.load(src)
        json.dump(config_data, dst, indent=2)
    
    return config_data