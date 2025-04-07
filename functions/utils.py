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

#does what it says on the tin
def load_config():
    import sys
    import os
    import json

    # First: check if there's an external config in the working directory
    local_path = os.path.join(os.getcwd(), "config.json")
    if os.path.exists(local_path):
        with open(local_path, "r") as f:
            return json.load(f)

    # Fallback: if running frozen, load bundled version
    if getattr(sys, "frozen", False):
        frozen_path = os.path.join(sys._MEIPASS, "config.json")
        with open(frozen_path, "r") as f:
            return json.load(f)

    # Last resort: look in script dir
    script_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    if os.path.exists(script_path):
        with open(script_path, "r") as f:
            return json.load(f)

    raise FileNotFoundError("config.json not found in any expected location.")


#used for verifiyng if a dir exists
# and creating it if it doesn't
def ensure_dir(path):
    """
    Ensures a persistent, writable directory (like LOCALAPPDATA/AutoConnect/data/path)
    """
    base_dir = os.path.join(os.environ.get("LOCALAPPDATA", "."), "AutoConnect", "data")
    full_path = os.path.join(base_dir, path)
    os.makedirs(full_path, exist_ok=True)
    return full_path


def get_persistent_data_path(filename):
    """
    Store app data in LOCALAPPDATA/AutoConnect/data/
    Works safely in both dev and frozen (.exe) environments
    """
    base_dir = os.path.join(os.environ.get("LOCALAPPDATA", "."), "AutoConnect", "data")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, filename)