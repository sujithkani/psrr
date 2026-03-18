"""
import configparser
import os
CFG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cfg.ini")

def load_network_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CFG_PATH):
        # fallback defaults
        return {"ip": "127.0.0.1", "port": 6006}
    config.read(CFG_PATH)
    try:
        ip = config.get("setup", "ip", fallback="127.0.0.1")
        port = config.getint("setup", "port", fallback=6006)
    except Exception:
        return {"ip": "127.0.0.1", "port": 6006}
    return {"ip": ip, "port": port}

def save_network_config(ip, port):
    import configparser
    import os

    config = configparser.ConfigParser()
    config["setup"] = {
        "ip": ip,
        "port": str(port)
    }

    os.makedirs(os.path.dirname(CFG_PATH), exist_ok=True)

    with open(CFG_PATH, "w") as f:
        config.write(f)
"""

import configparser
import os
import sys

def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as EXE → use exe directory
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.dirname(__file__))
CFG_PATH = os.path.join(get_base_path(), "data", "cfg.ini")

def load_network_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CFG_PATH):
        return {"ip": "127.0.0.1", "port": 6006}
    try:
        config.read(CFG_PATH)
        ip = config.get("setup", "ip", fallback="127.0.0.1")
        port = config.getint("setup", "port", fallback=6006)
        return {"ip": ip, "port": port}
    except Exception:
        return {"ip": "127.0.0.1", "port": 6006}

def save_network_config(ip, port):
    config = configparser.ConfigParser()
    config["setup"] = {
        "ip": str(ip),
        "port": str(port)
    }
    os.makedirs(os.path.dirname(CFG_PATH), exist_ok=True)
    try:
        with open(CFG_PATH, "w") as f:
            config.write(f)
    except Exception as e:
        print("CONFIG SAVE ERROR:", e)
