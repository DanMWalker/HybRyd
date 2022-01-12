from datetime import datetime
from os import path
import json

def timestamp():
    return datetime.now().strftime("%Y-%m-%d@%H:%M:%S")

insturment_manager = {}

app_config = {}

try:
    cfg_path = path.abspath(path.join(".", "config", "dashboard.cfg"))
    with open(cfg_path) as app_config_file:
        app_config = json.load(app_config_file)
except Exception as e:
    print("An exception occurred loading the external config file:\n", e)
    print("Reverting to built-in default config.")
    app_config = {
        "retained_messages": 1400,
        "software_instruments": []
    }