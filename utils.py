from keyboard import KeyboardEvent, KEY_DOWN
from keyboard._canonical_names import normalize_name
from modifiers import SHIFT, CTRL, ALT, WINDOWS
from functools import lru_cache
from my_logger import log_info
from typing import List, Sized, Tuple


def strict_matches_hotkeys(hotkeys: list[str], key_event: KeyboardEvent) -> bool:
    """
    matches if key_event with it's modifiers execatly matches
    the modifiers and key in hotkeys
    """
    for hotkey in hotkeys:
        if strict_matches_hotkey(hotkey, key_event):
            return True
    return False


def strict_matches_hotkey(hotkey: str, key_event: KeyboardEvent) -> bool:
    parts = hotkey.split("+")
    main_key = normalize_name(parts[-1])
    required_modifiers = {normalize_name(m) for m in parts[:-1]}

    if key_event.name != main_key:
        return False

    actual_mods = down_modifiers(key_event)
    return required_modifiers == actual_mods


def down_modifiers(event: KeyboardEvent):
    modifiers = event.modifiers
    if modifiers is None:
        log_info("modifiers where none some how")
        modifiers = []

    out = set()

    def add_if_needed(mod):
        if SHIFT in mod:
            out.add(SHIFT)
        elif CTRL in mod:
            out.add(CTRL)
        elif ALT in mod:
            out.add(ALT)
        elif WINDOWS in mod:
            out.add(WINDOWS)

    # if the caller presses shift it will report the name of shift but the
    # current modifier state of shift won't be down
    if event.event_type == KEY_DOWN:
        add_if_needed(event.name)

    for modifier in modifiers:
        add_if_needed(modifier)

    return out


@lru_cache
def compute_upper_count(s: str) -> int:
    return sum(1 for c in s if c.isupper())


def reversed_range(itr):
    return range(len(itr)-1, -1, -1)


def reverse_enumerate(s):
    for i in reversed_range(s):
        yield i, s[i]


def is_str(obj):
    return isinstance(obj, str)


def is_all_non_alphanumeric_str(s: str):
    return not any(ch.isalnum() for ch in s)


def safe_len(itr: Sized | None):
    if itr is None:
        return 0
    return len(itr)


def to_utf(name: str):
    if len(name) == 1:
        return name
    elif name == "space":
        return " "
    elif name == "tab":
        return "\t"
    elif name == "enter":
        return "\n"


def split_non_alpha(text: str, excluded: List[str]) -> List[Tuple[str, bool]]:
    """
    Returns a list of (token, is_separator).

    - token: the string piece
    - is_separator: True if it's a separator, False if it's a word

    Separators are characters that are:
    - NOT alphanumeric
    - AND NOT in the excluded list
    """
    excluded_set = set(excluded)

    tokens: List[Tuple[str, bool]] = []
    current: List[str] = []

    def flush_current():
        if current:
            tokens.append(("".join(current), False))
            current.clear()

    for ch in text:
        if ch.isalnum() or ch in excluded_set:
            current.append(ch)
        else:
            flush_current()
            tokens.append((ch, True))

    flush_current()
    return tokens


def alpha_numericish(ch: str):
    return ch.isalnum() or ch == "'"


"""
in normal words: delete previous or current word


inCamel: delete into you hit an uppercase if last letter was lower or upper if
it was lower, or if you hit a non_alphanumeric character

in_snake_case: delete until you hit _, SAME_HERE
unless we hit an uppercase/lowercase when the last letter was lower/upper


all-other-separators, will behave like snake case
"""


def backspaces_to_delete_previous_word(buffer: list[str]) -> int:
    if len(buffer) == 0:
        return 0

    i = len(buffer) - 1
    count = 0

    while i >= 0 and not buffer[i].isalnum():
        count += 1
        i -= 1

    all_non_alnum = i < 0
    if all_non_alnum:
        return len(buffer)

    upper_mode = buffer[i].isupper()

    if upper_mode:
        while i > 0:
            i -= 1
            count += 1
            ch = buffer[i]
            if not alpha_numericish(ch) or ch.isspace() or ch.islower():
                return count
    else:
        while i > 0:
            i -= 1
            count += 1
            ch = buffer[i]
            if ch.isspace() or not alpha_numericish(ch):
                return count
            if ch.isupper():
                return count + 1  # +1 to include the lower character

    return len(buffer)
