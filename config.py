# auto generated
import math
from spacing_type import SpacingType
from casing import Casing
from chunking import ChunkingType
from config_support import load_chips

class _ExpectedField:
    def __init__(self, default_value=None, cftype=None):
        self.default_value = default_value
        self.cftype = cftype


class _ExpectedList:
    def __init__(self, default_value=None, cftype=None, min_length=0, max_length=math.inf):
        default_value = default_value or []
        self.default_value = default_value
        self.cftype = cftype
        self.min_length = min_length
        self.max_length = max_length


class _ExpectedDict:
    def __init__(self, default_value=None, key_type=None, value_type=None, min_length=0, max_length=math.inf):
        default_value = default_value or {}
        self.default_value = default_value
        self.key_type = key_type
        self.cftype = value_type
        self.min_length = min_length
        self.max_length = max_length

def _check_type(value, expected_type) -> bool:
    if expected_type is None:
        return True
    if expected_type == bool:
        return isinstance(value, bool)
    if expected_type == int:
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == str:
        return isinstance(value, str)
    if expected_type == float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == list:
        return isinstance(value, list)
    if expected_type == dict:
        return isinstance(value, dict)
    return isinstance(value, expected_type)

def _merge_expected(config_map: dict, expected_map: dict, ignored_sections=set(), ignored_keys=set()) -> dict:
    result = {}

    for section_name, section_expected in expected_map.items():
        result[section_name] = {}
        for field_name, field_expected in section_expected.items():
            result[section_name][field_name] = field_expected.default_value

    for section_name, section_config in config_map.items():
        if section_name not in expected_map:
            if section_name in ignored_sections:
                result[section_name] = section_config.copy()
            else:
                print(f"Unused section: {section_name}")
            continue

        if not isinstance(section_config, dict):
            print(f"Type error in section '{section_name}': expected dict, got {type(section_config).__name__}")
            continue

        for field_name, field_value in section_config.items():
            if field_name not in expected_map[section_name]:
                if field_name in ignored_keys or section_name in ignored_sections:
                    result[section_name][field_name] = field_value
                else:
                    print(f"Unused field: {section_name}.{field_name}")
                continue

            field_expected = expected_map[section_name][field_name]

            if isinstance(field_expected, _ExpectedField):
                if _check_type(field_value, field_expected.cftype):
                    result[section_name][field_name] = field_value
                else:
                    print(f"Type error: {section_name}.{field_name} expected {field_expected.cftype}, got {type(field_value).__name__}")

            elif isinstance(field_expected, _ExpectedList):
                if not isinstance(field_value, list):
                    print(f"Type error: {section_name}.{field_name} expected list, got {type(field_value).__name__}")
                elif field_expected.cftype and not all(_check_type(v, field_expected.cftype) for v in field_value):
                    print(f"Type error: {section_name}.{field_name} expected list of {field_expected.cftype}")
                elif not (field_expected.min_length <= len(field_value) <= field_expected.max_length):
                    print(f"Length error: {section_name}.{field_name} length {len(field_value)} not in range [{field_expected.min_length}, {field_expected.max_length}]")
                else:
                    result[section_name][field_name] = field_value

            elif isinstance(field_expected, _ExpectedDict):
                if not isinstance(field_value, dict):
                    print(f"Type error: {section_name}.{field_name} expected dict, got {type(field_value).__name__}")
                elif field_expected.key_type and not all(_check_type(k, field_expected.key_type) for k in field_value.keys()):
                    print(f"Type error: {section_name}.{field_name} expected dict with keys of {field_expected.key_type}")
                elif field_expected.cftype and not all(_check_type(v, field_expected.cftype) for v in field_value.values()):
                    print(f"Type error: {section_name}.{field_name} expected dict with values of {field_expected.cftype}")
                elif not (field_expected.min_length <= len(field_value) <= field_expected.max_length):
                    print(f"Length error: {section_name}.{field_name} length {len(field_value)} not in range [{field_expected.min_length}, {field_expected.max_length}]")
                else:
                    result[section_name][field_name] = field_value

    return result

def _get_expected_map():
    return {"general": {"expand_on": _ExpectedList(["space"], str), "toggle_case_on": _ExpectedList(["shift"]), "clear_buffer_on": _ExpectedList(["windows_down", "ctrl_down", "alt_down"]), "capitalize_after": _ExpectedList([".", "!", "?"]), "append_chars": _ExpectedList([".", "!", "?", ",", ";", ")", "]", "}"]), "auto_append": _ExpectedField(False, bool)}, "chunking": {"chunking_type": _ExpectedField("last", str), "new_chunks_only": _ExpectedField(False, bool), "chunking_ignore": _ExpectedList(["'", "_"])}, "rare": {"just_set_safe_clear": _ExpectedList(["up", "down"]), "captlize_passthrough": _ExpectedList(["\"", "'", "`"])}, "code": {"spacing_type": _ExpectedField("normal", str), "assumed_casing": _ExpectedField("normal", str), "space_on_new": _ExpectedField(True, bool)}, "ipc": {"port": _ExpectedField(8765, int), "host": _ExpectedField("127.0.0.1", str), "ipc_enabled_commands": _ExpectedList([], str)}}

class Config:
    def __init__(self, config_map: dict | None = None):
        if not config_map:
            config_map = {}
        merged = _merge_expected(
            config_map, _get_expected_map()
            , ignored_keys=["'s", "n't", "'l", '-', 't,', "w'"], ignored_sections={'chips'}
        )
        self.general = GeneralSection(merged["general"])
        self.chunking = ChunkingSection(merged["chunking"])
        self.rare = RareSection(merged["rare"])
        self.code = CodeSection(merged["code"])
        self.ipc = IpcSection(merged["ipc"])
        self.chips: dict = load_chips(merged)

    def update(self, config_map: dict | None = None):
        if not config_map:
            config_map = {}
        merged = _merge_expected(
            config_map, _get_expected_map()
            , ignored_keys=["'s", "n't", "'l", '-', 't,', "w'"], ignored_sections={'chips'}
        )
        self.general.update(merged["general"])
        self.chunking.update(merged["chunking"])
        self.rare.update(merged["rare"])
        self.code.update(merged["code"])
        self.ipc.update(merged["ipc"])
        self.chips: dict = load_chips(merged)

class GeneralSection:
    def __init__(self, smap: dict):
        self.update(smap)

    def update(self, smap: dict):
        self.expand_on: list[str] = smap["expand_on"]
        self.toggle_case_on: list = smap["toggle_case_on"]
        self.clear_buffer_on: list = smap["clear_buffer_on"]
        self.capitalize_after: list = smap["capitalize_after"]
        self.append_chars: list = smap["append_chars"]
        self.auto_append: bool = smap["auto_append"]

class ChunkingSection:
    def __init__(self, smap: dict):
        self.update(smap)

    def update(self, smap: dict):
        self.chunking_type: ChunkingType = ChunkingType.safe_from_str(smap["chunking_type"], ChunkingType.LAST)
        self.new_chunks_only: bool = smap["new_chunks_only"]
        self.chunking_ignore: list = smap["chunking_ignore"]

class RareSection:
    def __init__(self, smap: dict):
        self.update(smap)

    def update(self, smap: dict):
        self.just_set_safe_clear: list = smap["just_set_safe_clear"]
        self.captlize_passthrough: list = smap["captlize_passthrough"]

class CodeSection:
    def __init__(self, smap: dict):
        self.update(smap)

    def update(self, smap: dict):
        self.spacing_type: SpacingType = SpacingType.safe_from_str(smap["spacing_type"], SpacingType.NORMAL)
        self.assumed_casing: Casing = Casing.safe_from_str(smap["assumed_casing"], Casing.NORMAL)
        self.space_on_new: bool = smap["space_on_new"]

class IpcSection:
    def __init__(self, smap: dict):
        self.update(smap)

    def update(self, smap: dict):
        self.port: int = smap["port"]
        self.host: str = smap["host"]
        self.ipc_enabled_commands: list[str] = smap["ipc_enabled_commands"]
