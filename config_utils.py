from config_manager import ConfigManager
from my_logger import log_info
from config import Config
import os
import tomllib


def _load_toml() -> dict:
    config_manager = ConfigManager("fuzzy_chips")
    CONFIG_FILE_NAME = "config.toml"
    path = ""
    if os.path.exists(CONFIG_FILE_NAME):
        path = CONFIG_FILE_NAME
    else:
        path = config_manager.find_config_file(CONFIG_FILE_NAME)

    if not os.path.exists(path):
        log_info("no config found")
        return {"chips": {}}

    with open(path, "rb") as file:
        data = tomllib.load(file)
    if "chips" not in data:
        data["chips"] = {}
    return data


def create_config() -> Config:
    data = _load_toml()
    return Config(data)


def reload_config(config: Config) -> None:
    data = _load_toml()
    config.update(data)
