import json
import os

USER_DATA_DIR = "user_data"

def _get_user_data_path(username, data_type):
    """Constructs the path for a user's specific data file."""
    user_dir = os.path.join(USER_DATA_DIR, username)
    os.makedirs(user_dir, exist_ok=True) # Ensure user directory exists
    return os.path.join(user_dir, f"{data_type}.json")

def save_user_data(username, data_type, data):
    """Saves user-specific data to a JSON file."""
    path = _get_user_data_path(username, data_type)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def load_user_data(username, data_type):
    """Loads user-specific data from a JSON file."""
    path = _get_user_data_path(username, data_type)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None # Return None if file does not exist