from config_manager import ConfigManager
from fuzzy_events import FuzzyEvent
from my_logger import log_info
from config import Config
from load_config_map import parse
import os
from pathlib import Path
from keyboard import KeyboardEvent, KEY_DOWN
from utils import strict_matches_hotkey
from keyboard.mouse import ButtonEvent, DOWN


def get_fuzzy_event_button(mouse_event: ButtonEvent, config: Config) -> list[FuzzyEvent]:
    if mouse_event.event_type != DOWN:
        return []
    out = []
    if mouse_event.button in config.on_mouse_button_down:
        out.append(config.on_mouse_button_down[mouse_event.button])
    return out


def get_fuzzy_event_keyboard(current_key: KeyboardEvent, prev_key: KeyboardEvent | None, down_keys: list[str], config: Config) -> list[FuzzyEvent]:
    is_press = current_key.event_type == KEY_DOWN
    name = current_key.name
    if prev_key:
        prev_name = prev_key.name
    else:
        prev_name = ""

    to_run = []

    for down_key in down_keys:
        if down_key in config.while_down:
            to_run.append(config.while_down[down_key])

    if is_press:
        for key, value in config.on_press.items():
            if strict_matches_hotkey(key, current_key):
                to_run.append(value)
                break

    if not is_press and prev_name == name and name in config.on_toggle:
        to_run.append(config.on_toggle[name])
    return to_run


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
