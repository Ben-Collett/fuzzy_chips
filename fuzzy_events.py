from enum import Enum


class FuzzyEvent(Enum):
    clear_buffer = "clear_buffer"
    expand = "expand"
    delete_word = "delete_word"
    clear_buffer_ipc_safe = "clear_buffer_ipc_safe"
    toggle_case = "toggle_case"

    @staticmethod
    def from_str(val: str) -> "FuzzyEvent|None":
        try:
            return FuzzyEvent(val)
        except ValueError:
            return None


def parse_on_press(config: dict) -> dict[str, FuzzyEvent]:
    section = config.get("on_press")
    out = {}
    if section is None:
        section = {
            "space": "expand",
            "shift+backspace": "delete_word",
            "up": "clear_buffer_ipc_safe",
            "down": "clear_buffer_ipc_safe",
        }
    if not isinstance(section, dict):
        return out
    for key, val in section.items():
        event = FuzzyEvent.from_str(val)
        if event is None:
            print(f"unknown event {key}={val} on_press, skipping")
            continue
        out[key] = val
    return out


def parse_on_toggle(config: dict) -> dict[str, FuzzyEvent]:
    section = config.get("on_toggle")
    out = {}

    if section is None:
        section = {
            "shift": "toggle_case"
        }
    if not isinstance(section, dict):
        return out
    for key, val in section.items():
        event = FuzzyEvent.from_str(val)
        if "+" in key and len(key) > 1:
            print(
                f" {key} hotkeys can not be on_toggle only single keys like shift, skipping")
            continue

        if event is None:
            print(f"unknown event {key}={val} on_press, skipping")
            continue
        out[key] = val
    return out


def parse_while_down(config: dict) -> dict[str, FuzzyEvent]:
    section = config.get("while_down")
    out = {}
    accepted_keys = ["windows", "alt", "ctrl"]
    if section is None:
        section = {
            "windows": "clear_buffer",
            "ctrl": "clear_buffer",
            "alt": "clear_buffer",
        }
    if not isinstance(section, dict):
        return out
    for key, val in section.items():
        event = FuzzyEvent.from_str(val)
        if key not in accepted_keys:
            print(
                f" {key} is not a known modifier only modifiers are allowed in while_down {accepted_keys}, skipping")
            continue

        if event is None:
            print(f"unknown event {key}={val} on_press, skipping")
            continue
        out[key] = val
    return out


def parse_on_mouse_button_down(config: dict) -> dict[str, FuzzyEvent]:
    section = config.get("on_mouse_button_down")
    out = {}

    if section is None:
        section = {
            "left": "clear_buffer"
        }
    if not isinstance(section, dict):
        return out
    for key, val in section.items():
        event = FuzzyEvent.from_str(val)
        if event is None:
            print(f"unknown event {key}={val} on_press, skipping")
            continue
        out[key] = val
    return out
