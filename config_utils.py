from config_manager import ConfigManager
from my_logger import log_info
from config import Config
from load_config_map import parse
import os
from pathlib import Path


def _load_toml() -> dict:
    config_manager = ConfigManager("fuzzy_chips")
    CONFIG_FILE_NAME = "config.toml"
    if os.path.exists(CONFIG_FILE_NAME):
        path = Path(CONFIG_FILE_NAME)
    else:
        path = config_manager.find_config_file(CONFIG_FILE_NAME)

    empty_chips = {"chips": {}}
    if not path.exists():
        log_info("no config found")
        return empty_chips

    data = parse(path, empty_chips) or empty_chips
    return data


def create_config() -> Config:
    data = _load_toml()
    return Config(data)


def reload_config(config: Config) -> None:
    data = _load_toml()
    config.update(data)
