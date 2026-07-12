
from keyboard import KeyboardEvent, KEY_DOWN, KEY_UP
from modifiers import SHIFT, ALT, CTRL, WINDOWS

_MODIFIERS = {SHIFT, ALT, CTRL, WINDOWS}


def make_event(name: str, event_type: str, down_mods: list[str] | None = None) -> KeyboardEvent:
    down_mods = down_mods or []
    return KeyboardEvent(event_type=event_type, scan_code=hash(name), name=name, modifiers=down_mods)


def make_down_event(name: str, down_mods: list[str] | None = None) -> KeyboardEvent:
    return make_event(name, KEY_DOWN, down_mods)


def make_up_event(name: str, down_mods: list[str] | None = None) -> KeyboardEvent:
    return make_event(name, KEY_UP, down_mods)


def make_down_up_events(name: str, down_mods: list[str] | None = None) -> tuple[KeyboardEvent, KeyboardEvent]:
    return (make_down_event(name, down_mods), make_up_event(name, down_mods))


_NAMED_EVENTS = {
    "bs": "backspace",
    "shift": "shift",
    "tab": "tab",
    "enter": "enter",
    "return": "enter",
    "esc": "escape",
    "escape": "escape",
    "del": "delete",
    "delete": "delete",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "home": "home",
    "end": "end",
    "pgup": "page up",
    "pgdn": "page down",
}


def events_from_text(text: str) -> list[KeyboardEvent]:
    out = []
    i = 0
    down_mods = set()

    def add_character(ch: str, target: list):
        shift_down = ch.isupper()

        if ch == " ":
            ch = "space"
        elif ch == "\t":
            ch = "tab"
        elif ch == "\n":
            ch = "enter"

        added_shift = shift_down and SHIFT not in down_mods
        if added_shift:
            down_mods.add(SHIFT)

        target.append(make_down_event(ch, list(down_mods)))
        if added_shift:
            down_mods.remove(SHIFT)
        target.append(make_up_event(ch, list(down_mods)))

    while i < len(text):
        if text[i] == '<':
            end = text.find('>', i)
            if end == -1:
                ch = text[i]
                add_character(ch, target=out)
                i += 1
                continue

            inner = text[i + 1:end]

            if ':' in inner:
                name, action_str = inner.split(':', 1)
                resolved_name = _NAMED_EVENTS.get(name, name)

                if action_str == "down":
                    if resolved_name in _MODIFIERS:
                        down_mods.add(resolved_name)
                    out.append(make_down_event(resolved_name, list(down_mods)))
                elif action_str == "up":
                    if resolved_name in _MODIFIERS:
                        down_mods.discard(resolved_name)
                    out.append(make_up_event(resolved_name, list(down_mods)))
                else:
                    try:
                        count = int(action_str)
                    except ValueError:
                        count = 1
                    mods = list(down_mods)
                    for _ in range(count):
                        out.extend(make_down_up_events(resolved_name, mods))
            else:
                name = inner
                count = 1
                resolved_name = _NAMED_EVENTS.get(name, name)
                mods = list(down_mods)
                for _ in range(count):
                    out.extend(make_down_up_events(resolved_name, mods))

            i = end + 1
        else:
            ch = text[i]
            add_character(ch, target=out)
            i += 1

    return out
