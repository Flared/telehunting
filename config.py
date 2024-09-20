import json
import os
from utils import print_success, print_info

def load_config(config_path):
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return None

def create_default_config(config_path):
    default_config = {
        "initial_channel_links": [],
        "message_keywords": [],
        "batch_size": 100
    }
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=4)
    print_success(f"Default config file created at {config_path}")
    print_info("Please edit this file with your channel links and keywords.")
    return default_config
