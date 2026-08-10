from config_utils import get_fuzzy_event_button, get_fuzzy_event_keyboard, reload_config, create_config
from config import Config
from frozen_dict import FrozenDict
from fuzzy_events import FuzzyEvent
from keyboard.mouse import ButtonEvent
from keyboard import KeyboardEvent
from linux_keyboard import LinuxKeyboardType
from spacing_type import SpacingType


class ConfigWrapper:
    @staticmethod
    def load() -> "ConfigWrapper":
        return ConfigWrapper(create_config())

    @staticmethod
    def default_config(config_override: dict | None = None) -> "ConfigWrapper":
        return ConfigWrapper(Config(config_override))

    def __init__(self, config: Config):
        self._config = config

    def get_buffer_size(self) -> int:
        return self._config.general.buffer_size

    def get_ipc_enabled_commands(self) -> list[str]:
        return self._config.ipc.ipc_enabled_commands

    def get_capitalize_after(self):
        return self._config.general.capitalize_after

    def get_capitalize_passthrough(self):
        return self._config.rare.capitalize_passthrough

    def get_fuzzy_event_button(self, mouse_event: ButtonEvent) -> list[FuzzyEvent]:
        return get_fuzzy_event_button(mouse_event, self._config)

    def get_append_chars(self):
        return self._config.general.append_chars

    def should_auto_append(self, ch: str):
        return self._config.general.auto_append and ch in self.get_append_chars()

    def get_host(self) -> str:
        return self._config.ipc.host

    def linux_keyboard_type(self) -> LinuxKeyboardType:
        return self._config.linux.keyboard_type

    def get_code_spacing_type(self) -> SpacingType:
        return self._config.code.spacing_type

    def get_port(self) -> int:
        return self._config.ipc.port

    def is_chip(self, freq: FrozenDict) -> bool:
        return freq in self._config.chips.keys()

    def expand_new_chunks_only(self) -> bool:
        return self._config.chunking.new_chunks_only

    def get_chunking_ignore(self) -> list[str]:
        return self._config.chunking.chunking_ignore

    def get_chunking_type(self):
        return self._config.chunking.chunking_type

    def get_assumed_casing(self):
        return self._config.code.assumed_casing

    def str_is_chip(self, s: str) -> bool:
        return self.is_chip(FrozenDict.from_string(s))

    def get_chip(self, freq: FrozenDict) -> list[str] | str | None:
        return self._config.chips.get(freq)

    def get_chip_from_str(self, s: str) -> list[str] | str | None:
        return self.get_chip(FrozenDict.from_string(s))

    def get_space_on_new(self) -> bool:
        return self._config.code.space_on_new

    def get_fuzzy_event_keyboard(self, current_key: KeyboardEvent, prev_key: KeyboardEvent | None, down_keys: list[str]) -> list[FuzzyEvent]:
        return get_fuzzy_event_keyboard(current_key, prev_key, down_keys, self._config)

    def reload_config(self, override: dict | None = None):
        reload_config(self._config, data=override)
