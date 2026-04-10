import tomllib
import os
from frozen_dict import FrozenDict
from my_logger import log_info
from my_config_manager import config_manager
from spacing_type import SpacingType
from casing import Casing
from constants import DEFAULT_PORT, LOCAL_HOST
from errors import parse_assumed_casing_error_message


def _load_toml() -> dict:
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


def _chip_map(chips) -> dict[FrozenDict, str]:
    out = {}
    for k, v in chips.items():
        key = FrozenDict.from_string(k)
        if key in out.keys():
            old_val = out[key]
            log_info(f"colliding key overridng: {
                k}={old_val} with {k} = {v}")

        out[key] = v
    return out


def _get_section(section, config_map):
    if section in config_map:
        return config_map[section]
    return {}


def _get_from_toml(section, name, config_map, default=None):
    if section in config_map and name in config_map[section]:
        return config_map[section][name]
    return default


class Config:
    def __init__(self, config_map=None):
        self.update(config_map)

    def reload(self):
        self.update(_load_toml())

    def update(self, config_map=None):
        config_map = config_map or {}

        def get_code(name, default=None):
            return _get_from_toml("code", name, config_map, default)

        def get_general(name, default=None):
            return _get_from_toml("general", name, config_map, default)

        def get_ipc(name, default=None):
            return _get_from_toml("ipc", name, config_map, default)

        self.chip_map = _chip_map(_get_section("chips", config_map))
        self.append_chars = get_general(
            "append_chars", [".", ",", "!", "?", ";"])
        self.capitalize_after = get_general(
            "capitalize_after", [".", "!", "?"])
        self.capitalize_passthrough = get_general(
            "captlize_passthrough", ["'", '"', "`"])
        self.auto_apped = get_general("auto_append", True)
        self.toggle_case_on = get_general("toggle_case_on", ["shift"])

        self.clear_buffer_on_keys:str = get_general(
            "clear_buffer_on", ["windows_down", "alt_down", "ctrl_down"])
        self.just_set_safe_clear = get_general(
            "just_set_safe_clear", ["up", "down"])

        self.shift_backspace_included_delimiters = get_general(
            # different kinds of dashes minus,  emdash, endash hyphen
            "shift_backspace_included_delimiters", ["_", "-", "—", "−", "‐", "uppercase"])
        self.shift_backspace_excluded_delimiters = get_general(
            "shift_backspace_excluded_delimiters", [" "])
        self.separate_tail = get_general("separate_tail", ["uppercase"])

        self.ignored_leading = get_general("ignored_leading",  [
                                           '"', "(", "[", "{", "`", "'"])
        self.ignored_trailing = get_general(
            "ignored_trailing",  ['"', ")", "]", "}", "`", "'", ".", "!", "?", ","])

        spacing_type = get_code("spacing_type", "normal")
        self.spacing_type = SpacingType.safe_from_str(
            spacing_type, default=SpacingType.NORMAL, print_on_err=True)

        assumed_casing:str = get_code("assumed_casing", "normal")
        self.assumed_casing = Casing.safe_from_str(
            assumed_casing, default=Casing.NORMAL, generate_err_message=parse_assumed_casing_error_message)
        self.space_on_new = get_code("space_on_new", True)
        self.port = get_ipc("port", DEFAULT_PORT)
        self.host = get_ipc("host", LOCAL_HOST)
        self.ipc_enabled_commands:list[str] = get_ipc("ipc_enabled_commands", default=[])
        self.buffer_state_timeout_ms = get_general(
            "buffer_state_timeout_ms", 1)


current_config = Config(_load_toml())
