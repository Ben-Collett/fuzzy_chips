import tomllib
import os
from chunking import ChunkingType
from frozen_dict import FrozenDict
from my_logger import log_info
from config_manager import ConfigManager
from spacing_type import SpacingType
from casing import Casing
from constants import DEFAULT_PORT, LOCAL_HOST


def _load_toml(config_manager: ConfigManager) -> dict:
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
            log_info(f"colliding key overridng: {k}={old_val} with {k} = {v}")

        out[key] = v
    return out


def _get_section(section, config_map):
    if section in config_map:
        return config_map[section]
    return {}


def _get_from_toml[T](
    section: str, name: str, config_map: dict, default: T, expected_type: type[T]
) -> T:
    if section in config_map and name in config_map[section]:
        value = config_map[section][name]
        if isinstance(value, expected_type):
            return value
        log_info(
            f"config [{section}].[name] expected {expected_type.__name__}, got {type(value).__name__}; using default"
        )
    return default


class Config:
    def __init__(self, config_map=None, config_manager=None):
        self._config_manager = config_manager
        self.update(config_map)

    @classmethod
    def load(cls, config_manager: ConfigManager) -> "Config":
        return cls(_load_toml(config_manager), config_manager)

    def reload(self):
        if self._config_manager is None:
            raise RuntimeError("config_manager not set, cannot reload")
        self.update(_load_toml(self._config_manager))

    def update(self, config_map=None):
        config_map = config_map or {}

        def get_code[T](name: str, default: T, expected_type: type[T]) -> T:
            return _get_from_toml("code", name, config_map, default, expected_type)

        def get_general[T](name: str, default: T, expected_type: type[T]) -> T:
            return _get_from_toml("general", name, config_map, default, expected_type)

        def get_ipc[T](name: str, default: T, expected_type: type[T]) -> T:
            return _get_from_toml("ipc", name, config_map, default, expected_type)

        def get_rare[T](name: str, default: T, expected_type: type[T]) -> T:
            return _get_from_toml("rare", name, config_map, default, expected_type)

        def get_chunking[T](name: str, default: T, expected_type: type[T]) -> T:
            return _get_from_toml("chunking", name, config_map, default, expected_type)

        self.chip_map = _chip_map(_get_section("chips", config_map))
        self.append_chars: list[str] = get_general(
            "append_chars", [".", ",", "!", "?", ";"], list
        )
        self.capitalize_after: list[str] = get_general(
            "capitalize_after", [".", "!", "?"], list
        )
        self.capitalize_passthrough: list[str] = get_rare(
            "captlize_passthrough", ["'", '"', "`"], list
        )
        self.auto_append: bool = get_general("auto_append", True, bool)
        self.toggle_case_on: list[str] = get_general("toggle_case_on", ["shift"], list)

        self.clear_buffer_on_keys: list[str] = get_general(
            "clear_buffer_on", ["windows_down", "alt_down", "ctrl_down"], list
        )

        self.just_set_safe_clear: list[str] = get_rare(
            "just_set_safe_clear", ["up", "down"], list
        )

        spacing_type: str = get_code("spacing_type", "normal", str)
        self.spacing_type = SpacingType.safe_from_str(
            spacing_type, SpacingType.NORMAL, print_on_err=True
        )

        assumed_casing: str = get_code("assumed_casing", "normal", str)
        self.assumed_casing = Casing.safe_from_str(assumed_casing, Casing.NORMAL)
        self.space_on_new: bool = get_code("space_on_new", True, bool)
        self.port: int = get_ipc("port", DEFAULT_PORT, int)
        self.host: str = get_ipc("host", LOCAL_HOST, str)
        self.ipc_enabled_commands: list[str] = get_ipc("ipc_enabled_commands", [], list)

        chunking_type: str = get_chunking("chunking_mode", "last", str)
        self.chunking_type = ChunkingType.safe_from_str(chunking_type, ChunkingType.ALL)
        self.new_chunks_only: bool = get_chunking("new_chunks_only", False, bool)
        self.chunking_ignore: list[str] = get_chunking("chunking_ignore", ["'"], list)
