import tomllib
import os
from frozen_dict import FrozenDict
from my_config_manager import config_manager


def _load_toml() -> dict:
    CONFIG_FILE_NAME = "config.toml"
    path = ""
    if os.path.exists(CONFIG_FILE_NAME):
        path = CONFIG_FILE_NAME
    else:
        path = config_manager.find_config_file(CONFIG_FILE_NAME)

    if not os.path.exists(path):
        print("no config found")
        return {"chips": {}}

    with open(path, "rb") as file:
        data = tomllib.load(file)
    if "chips" not in data:
        data["chips"] = {}
    return data


def _chip_map(chips) -> dict[FrozenDict[str], str]:
    out = {}
    for k, v in chips.items():
        key = FrozenDict.from_string(k)
        if key in out.keys():
            old_val = out[key]
            print(f"colliding key overridng: {
                k}={old_val} with {k} = {v}")

        out[key] = v
    return out


class Config:
    def __init__(self, config_map):
        self.update(config_map)

    def reload(self):
        self.update(_load_toml())

    def update(self, config_map):
        def get_general(name, default=None):
            if "general" in config_map and name in config_map["general"]:
                return config_map["general"][name]
            return default

        self.chip_map = _chip_map(config_map["chips"])
        self.append_chars = get_general(
            "append_chars", [".", ",", "!", "?", ";"])
        self.capitalize_after = get_general(
            "capitalize_after", [".", "!", "?"])
        self.capitalize_passthrough = get_general(
            "captlize_passthrough", ["'", '"', "`"])
        self.auto_apped = get_general("auto_append", True)
        self.toggle_case_on = get_general("toggle_case_on", ["shift"])
        self.clear_buffer_on_keys = get_general("clear_buffer_on", [
                                                "windows_down", "alt_down", "ctrl_down", "left", "right", "up", "down"])
        self.shift_backspace_included_delimiters = get_general(
            # different kinds of dashes minus,  emdash, endash hyphen
            "shift_backspace_included_delimiters", ["_", "-", "—", "−", "‐", "uppercase"])
        self.shift_backspace_excluded_delimiters = get_general(
            "shift_backspace_excluded_delimiters", [" "])
        self.separate_tail = get_general("separate_tail", ["uppercase"])


current_config = Config(_load_toml())
