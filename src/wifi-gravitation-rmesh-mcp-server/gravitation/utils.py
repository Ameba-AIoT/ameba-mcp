import psutil
import socket
import os
import shutil
import sys
from pathlib import Path
import yaml

def get_interfaces():
    """
    遍历所有网络接口，返回接口列表
    Obtain all network interfaces and return a list of interface names.
    """
    interfaces = []
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                interfaces.append(iface)
                break
    return interfaces

def resource_path(relative_path):
    """ Get absolute path to resource, works for both dev env and for PyInstaller packed env """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path('.').resolve()

    return base_path / relative_path


def ensure_user_config():
    """ Ensure the user has a copy of the config file they can modify in the current directory """
    # user_config_path = os.path.join(os.getcwd(), 'config.yaml')
    # if not os.path.exists(user_config_path):
    #     # if user config does not exist, copy the default config in bundle to the current directory
    #     default_config_path = resource_path('config.yaml')
    #     shutil.copy(default_config_path, user_config_path)
    # return user_config_path
    return ""

def load_config():
    """ Load and parse the configuration file """
    config_path = ensure_user_config()
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config


def save_config(config):
    """ Save the configuration back to the file """
    config_path = ensure_user_config()
    with open(config_path, 'w') as config_file:
        yaml.safe_dump(config, config_file)


def update_config_key(key_path, value):
    """
    Update a specific key in the user configuration.

    :param key_path: List of keys representing the path to the target key in the nested dictionary.
    :param value: The new value to set for the specified key.
    """
    keys = key_path.split('.')
    config = load_config()
    sub_config = config
    for key in keys[:-1]:
        sub_config = sub_config.setdefault(key, {})
    sub_config[keys[-1]] = value
    save_config(config)


def optional_chain(d, *keys):
    """ Safely access nested dictionary keys """
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, None)
        else:
            return None
    return d


def is_frozen():
    return hasattr(sys, '_MEIPASS')
