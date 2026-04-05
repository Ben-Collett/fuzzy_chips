from collections import deque
from keyboard import KeyboardEvent, KEY_DOWN
from modifiers import SHIFT, CTRL, ALT, WINDOWS
from functools import lru_cache


def print_debug(*args, **kwargs):
    print(*args, **kwargs)


def down_modifiers(event: KeyboardEvent):
    modifiers = event.modifiers
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


def end_with_count(itr, val):
    count = 0
    for i in reversed(itr):
        if val == itr[i]:
            count += 1
    return count


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


def to_utf(event: KeyboardEvent, shift_down):
    name = event.name
    if len(name) == 1:
        if shift_down:
            return name.upper()
        else:
            return name
    elif name == "space":
        return " "
    elif name == "tab":
        return "\t"
    elif name == "enter":
        return "\n"


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
    if not buffer:
        return 0

    i = len(buffer) - 1
    count = 0

    while i >= 0 and not buffer[i].isalnum():
        count += 1
        i -= 1

    if i < 0:
        return len(buffer) - i

    upper_mode = buffer[i].isupper()

    if upper_mode:
        while i > 0:
            i -= 1
            count += 1
            ch = buffer[i]
            if ch.islower() or ch.isspace():
                return count-1
            if not alpha_numericish(ch):
                return count
    else:
        while i > 0:
            i -= 1
            count += 1
            ch = buffer[i]
            if ch.isspace():
                return count-1
            if ch.isupper() or not alpha_numericish(ch):
                return count

    return len(buffer) - 1
