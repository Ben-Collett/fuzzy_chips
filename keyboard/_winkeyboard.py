# -*- coding: utf-8 -*-
"""
This is the Windows backend for keyboard events, and is implemented by
invoking the Win32 API through the ctypes module. This is error prone
and can introduce very unpythonic failure modes, such as segfaults and
low level memory leaks. But it is also dependency-free, very performant
well documented on Microsoft's website and scattered examples.

# TODO:
- Keypad numbers still print as numbers even when numlock is off.
- No way to specify if user wants a keypad key or not in `map_char`.
"""

from ctypes.wintypes import (
    WORD,
    DWORD,
    BOOL,
    HHOOK,
    MSG,
    LPWSTR,
    WCHAR,
    WPARAM,
    LPARAM,
    LONG,
    HMODULE,
    LPCWSTR,
    HINSTANCE,
    HWND,
)
from ctypes import (
    c_short,
    c_char,
    c_uint8,
    c_int32,
    c_int,
    c_uint,
    c_uint32,
    c_long,
    Structure,
    WINFUNCTYPE,
    POINTER,
)
import ctypes
import atexit
import traceback
from threading import Condition, Lock, get_ident
from collections import defaultdict

from ._keyboard_event import KeyboardEvent, KEY_DOWN, KEY_UP
from ._canonical_names import all_modifiers, normalize_name
from ._windows_synthetic_modes import WindowsSyntheticModes

synthetic_mode = WindowsSyntheticModes.FAKE

# This part is just declaring Win32 API structures using ctypes. In C
# this would be simply #include "windows.h".

LPMSG = POINTER(MSG)
ULONG_PTR = POINTER(DWORD)

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
GetModuleHandleW = kernel32.GetModuleHandleW
GetModuleHandleW.restype = HMODULE
GetModuleHandleW.argtypes = [LPCWSTR]

# https://github.com/boppreh/mouse/issues/1
# user32 = ctypes.windll.user32
user32 = ctypes.WinDLL("user32", use_last_error=True)

VK_PACKET = 0xE7

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

KEYEVENTF_KEYUP = 0x02
KEYEVENTF_UNICODE = 0x04


class KBDLLHOOKSTRUCT(Structure):
    _fields_ = [
        ("vk_code", DWORD),
        ("scan_code", DWORD),
        ("flags", DWORD),
        ("time", c_int),
        ("dwExtraInfo", ULONG_PTR),
    ]


# Included for completeness.


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ("dx", LONG),
        ("dy", LONG),
        ("mouseData", DWORD),
        ("dwFlags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (
        ("wVk", WORD),
        ("wScan", WORD),
        ("dwFlags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg", DWORD), ("wParamL", WORD), ("wParamH", WORD))


class _INPUTunion(ctypes.Union):
    _fields_ = (("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT))


class INPUT(ctypes.Structure):
    _fields_ = (("type", DWORD), ("union", _INPUTunion))


LowLevelKeyboardProc = WINFUNCTYPE(
    c_int, WPARAM, LPARAM, POINTER(KBDLLHOOKSTRUCT))

SetWindowsHookEx = user32.SetWindowsHookExW
SetWindowsHookEx.argtypes = [c_int, LowLevelKeyboardProc, HINSTANCE, DWORD]
SetWindowsHookEx.restype = HHOOK

CallNextHookEx = user32.CallNextHookEx
# CallNextHookEx.argtypes = [c_int , c_int, c_int, POINTER(KBDLLHOOKSTRUCT)]
CallNextHookEx.restype = c_int

UnhookWindowsHookEx = user32.UnhookWindowsHookEx
UnhookWindowsHookEx.argtypes = [HHOOK]
UnhookWindowsHookEx.restype = BOOL

GetMessage = user32.GetMessageW
GetMessage.argtypes = [LPMSG, HWND, c_uint, c_uint]
GetMessage.restype = BOOL

TranslateMessage = user32.TranslateMessage
TranslateMessage.argtypes = [LPMSG]
TranslateMessage.restype = BOOL

DispatchMessage = user32.DispatchMessageA
DispatchMessage.argtypes = [LPMSG]


keyboard_state_type = c_uint8 * 256

GetKeyboardState = user32.GetKeyboardState
GetKeyboardState.argtypes = [keyboard_state_type]
GetKeyboardState.restype = BOOL

GetKeyNameText = user32.GetKeyNameTextW
GetKeyNameText.argtypes = [c_long, LPWSTR, c_int]
GetKeyNameText.restype = c_int

MapVirtualKey = user32.MapVirtualKeyW
MapVirtualKey.argtypes = [c_uint, c_uint]
MapVirtualKey.restype = c_uint

ToUnicode = user32.ToUnicode
ToUnicode.argtypes = [c_uint, c_uint,
                      keyboard_state_type, LPWSTR, c_int, c_uint]
ToUnicode.restype = c_int

SendInput = user32.SendInput
SendInput.argtypes = [c_uint, POINTER(INPUT), c_int]
SendInput.restype = c_uint

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms646307(v=vs.85).aspx
MAPVK_VK_TO_CHAR = 2
MAPVK_VK_TO_VSC = 0
MAPVK_VSC_TO_VK = 1
MAPVK_VK_TO_VSC_EX = 4
MAPVK_VSC_TO_VK_EX = 3

VkKeyScan = user32.VkKeyScanW
VkKeyScan.argtypes = [WCHAR]
VkKeyScan.restype = c_short

LLKHF_INJECTED = 0x00000010
LLKHF_UNICODE = 0x4

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x104  # Used for ALT key
WM_SYSKEYUP = 0x105


# This marks the end of Win32 API declarations. The rest is ours.

keyboard_event_types = {
    WM_KEYDOWN: KEY_DOWN,
    WM_KEYUP: KEY_UP,
    WM_SYSKEYDOWN: KEY_DOWN,
    WM_SYSKEYUP: KEY_UP,
}

# List taken from the official documentation, but stripped of the OEM-specific keys.
# Keys are virtual key codes, values are pairs (name, is_keypad).
official_virtual_keys = {
    0x03: ("control-break processing", False),
    0x08: ("backspace", False),
    0x09: ("tab", False),
    0x0C: ("clear", False),
    0x0D: ("enter", False),
    0x10: ("shift", False),
    0x11: ("ctrl", False),
    0x12: ("alt", False),
    0x13: ("pause", False),
    0x14: ("caps lock", False),
    0x15: ("ime kana mode", False),
    0x15: ("ime hanguel mode", False),
    0x15: ("ime hangul mode", False),
    0x17: ("ime junja mode", False),
    0x18: ("ime final mode", False),
    0x19: ("ime hanja mode", False),
    0x19: ("ime kanji mode", False),
    0x1B: ("esc", False),
    0x1C: ("ime convert", False),
    0x1D: ("ime nonconvert", False),
    0x1E: ("ime accept", False),
    0x1F: ("ime mode change request", False),
    0x20: ("spacebar", False),
    0x21: ("page up", False),
    0x22: ("page down", False),
    0x23: ("end", False),
    0x24: ("home", False),
    0x25: ("left", False),
    0x26: ("up", False),
    0x27: ("right", False),
    0x28: ("down", False),
    0x29: ("select", False),
    0x2A: ("print", False),
    0x2B: ("execute", False),
    0x2C: ("print screen", False),
    0x2D: ("insert", False),
    0x2E: ("delete", False),
    0x2F: ("help", False),
    0x30: ("0", False),
    0x31: ("1", False),
    0x32: ("2", False),
    0x33: ("3", False),
    0x34: ("4", False),
    0x35: ("5", False),
    0x36: ("6", False),
    0x37: ("7", False),
    0x38: ("8", False),
    0x39: ("9", False),
    0x41: ("a", False),
    0x42: ("b", False),
    0x43: ("c", False),
    0x44: ("d", False),
    0x45: ("e", False),
    0x46: ("f", False),
    0x47: ("g", False),
    0x48: ("h", False),
    0x49: ("i", False),
    0x4A: ("j", False),
    0x4B: ("k", False),
    0x4C: ("l", False),
    0x4D: ("m", False),
    0x4E: ("n", False),
    0x4F: ("o", False),
    0x50: ("p", False),
    0x51: ("q", False),
    0x52: ("r", False),
    0x53: ("s", False),
    0x54: ("t", False),
    0x55: ("u", False),
    0x56: ("v", False),
    0x57: ("w", False),
    0x58: ("x", False),
    0x59: ("y", False),
    0x5A: ("z", False),
    0x5B: ("left windows", False),
    0x5C: ("right windows", False),
    0x5D: ("applications", False),
    0x5F: ("sleep", False),
    0x60: ("0", True),
    0x61: ("1", True),
    0x62: ("2", True),
    0x63: ("3", True),
    0x64: ("4", True),
    0x65: ("5", True),
    0x66: ("6", True),
    0x67: ("7", True),
    0x68: ("8", True),
    0x69: ("9", True),
    0x6A: ("*", True),
    0x6B: ("+", True),
    0x6C: ("separator", True),
    0x6D: ("-", True),
    0x6E: ("decimal", True),
    0x6F: ("/", True),
    0x70: ("f1", False),
    0x71: ("f2", False),
    0x72: ("f3", False),
    0x73: ("f4", False),
    0x74: ("f5", False),
    0x75: ("f6", False),
    0x76: ("f7", False),
    0x77: ("f8", False),
    0x78: ("f9", False),
    0x79: ("f10", False),
    0x7A: ("f11", False),
    0x7B: ("f12", False),
    0x7C: ("f13", False),
    0x7D: ("f14", False),
    0x7E: ("f15", False),
    0x7F: ("f16", False),
    0x80: ("f17", False),
    0x81: ("f18", False),
    0x82: ("f19", False),
    0x83: ("f20", False),
    0x84: ("f21", False),
    0x85: ("f22", False),
    0x86: ("f23", False),
    0x87: ("f24", False),
    0x90: ("num lock", False),
    0x91: ("scroll lock", False),
    0xA0: ("left shift", False),
    0xA1: ("right shift", False),
    0xA2: ("left ctrl", False),
    0xA3: ("right ctrl", False),
    0xA4: ("left menu", False),
    0xA5: ("right menu", False),
    0xA6: ("browser back", False),
    0xA7: ("browser forward", False),
    0xA8: ("browser refresh", False),
    0xA9: ("browser stop", False),
    0xAA: ("browser search key", False),
    0xAB: ("browser favorites", False),
    0xAC: ("browser start and home", False),
    0xAD: ("volume mute", False),
    0xAE: ("volume down", False),
    0xAF: ("volume up", False),
    0xB0: ("next track", False),
    0xB1: ("previous track", False),
    0xB2: ("stop media", False),
    0xB3: ("play/pause media", False),
    0xB4: ("start mail", False),
    0xB5: ("select media", False),
    0xB6: ("start application 1", False),
    0xB7: ("start application 2", False),
    0xBB: ("+", False),
    0xBC: (",", False),
    0xBD: ("-", False),
    0xBE: (".", False),
    # 0xbe:('/', False), # Used for miscellaneous characters; it can vary by keyboard. For the US standard keyboard, the '/?.
    0xE5: ("ime process", False),
    0xF6: ("attn", False),
    0xF7: ("crsel", False),
    0xF8: ("exsel", False),
    0xF9: ("erase eof", False),
    0xFA: ("play", False),
    0xFB: ("zoom", False),
    0xFC: ("reserved ", False),
    0xFD: ("pa1", False),
    0xFE: ("clear", False),
}

tables_lock = Lock()
to_name = defaultdict(list)
from_name = defaultdict(list)
scan_code_to_vk = {}

distinct_modifiers = [
    (),
    ("shift",),
    ("alt gr",),
    ("num lock",),
    ("shift", "num lock"),
    ("caps lock",),
    ("shift", "caps lock"),
    ("alt gr", "num lock"),
]

name_buffer = ctypes.create_unicode_buffer(32)
unicode_buffer = ctypes.create_unicode_buffer(32)
keyboard_state = keyboard_state_type()


def get_event_names(scan_code, vk, is_extended, modifiers):
    is_keypad = (scan_code, vk, is_extended) in keypad_keys
    is_official = vk in official_virtual_keys
    if is_keypad and is_official:
        yield official_virtual_keys[vk][0]

    keyboard_state[0x10] = 0x80 * ("shift" in modifiers)
    keyboard_state[0x11] = 0x80 * ("alt gr" in modifiers)
    keyboard_state[0x12] = 0x80 * ("alt gr" in modifiers)
    keyboard_state[0x14] = 0x01 * ("caps lock" in modifiers)
    keyboard_state[0x90] = 0x01 * ("num lock" in modifiers)
    keyboard_state[0x91] = 0x01 * ("scroll lock" in modifiers)
    unicode_ret = ToUnicode(
        vk, scan_code, keyboard_state, unicode_buffer, len(unicode_buffer), 0
    )
    if unicode_ret and unicode_buffer.value:
        yield unicode_buffer.value
        # unicode_ret == -1 -> is dead key
        # ToUnicode has the side effect of setting global flags for dead keys.
        # Therefore we need to call it twice to clear those flags.
        # If your 6 and 7 keys are named "^6" and "^7", this is the reason.
        ToUnicode(vk, scan_code, keyboard_state,
                  unicode_buffer, len(unicode_buffer), 0)

    name_ret = GetKeyNameText(
        scan_code << 16 | is_extended << 24, name_buffer, 1024)
    if name_ret and name_buffer.value:
        yield name_buffer.value

    char = user32.MapVirtualKeyW(vk, MAPVK_VK_TO_CHAR) & 0xFF
    if char != 0:
        yield chr(char)

    if not is_keypad and is_official:
        yield official_virtual_keys[vk][0]


def _setup_name_tables():
    """
    Ensures the scan code/virtual key code/name translation tables are
    filled.
    """
    with tables_lock:
        if to_name:
            return

        # Go through every possible scan code, and map them to virtual key codes.
        # Then vice-versa.
        all_scan_codes = [
            (sc, user32.MapVirtualKeyExW(sc, MAPVK_VSC_TO_VK_EX, 0))
            for sc in range(0x100)
        ]
        all_vks = [
            (user32.MapVirtualKeyExW(vk, MAPVK_VK_TO_VSC_EX, 0), vk)
            for vk in range(0x100)
        ]
        for scan_code, vk in all_scan_codes + all_vks:
            # `to_name` and `from_name` entries will be a tuple (scan_code, vk, extended, shift_state).
            if (scan_code, vk, 0, 0, 0) in to_name:
                continue

            if scan_code not in scan_code_to_vk:
                scan_code_to_vk[scan_code] = vk

            # Brute force all combinations to find all possible names.
            for extended in [0, 1]:
                for modifiers in distinct_modifiers:
                    entry = (scan_code, vk, extended, modifiers)
                    # Get key names from ToUnicode, GetKeyNameText, MapVirtualKeyW and official virtual keys.
                    names = list(get_event_names(*entry))
                    if names:
                        # Also map lowercased key names, but only after the properly cased ones.
                        lowercase_names = [name.lower() for name in names]
                        to_name[entry] = names + lowercase_names
                        # Remember the "id" of the name, as the first techniques
                        # have better results and therefore priority.
                        for i, name in enumerate(
                            map(normalize_name, names + lowercase_names)
                        ):
                            from_name[name].append((i, entry))

        # TODO: single quotes on US INTL is returning the dead key (?), and therefore
        # not typing properly.

        # Alt gr is way outside the usual range of keys (0..127) and on my
        # computer is named as 'ctrl'. Therefore we add it manually and hope
        # Windows is consistent in its inconsistency.
        for extended in [0, 1]:
            for modifiers in distinct_modifiers:
                to_name[(541, 162, extended, modifiers)] = ["alt gr"]
                from_name["alt gr"].append(
                    (1, (541, 162, extended, modifiers)))

    modifiers_preference = defaultdict(lambda: 10)
    modifiers_preference.update(
        {(): 0, ("shift",): 1, ("alt gr",): 2, ("ctrl",): 3, ("alt",): 4}
    )

    def order_key(line):
        i, entry = line
        scan_code, vk, extended, modifiers = entry
        return modifiers_preference[modifiers], i, extended, vk, scan_code

    for name, entries in list(from_name.items()):
        from_name[name] = sorted(set(entries), key=order_key)


# Called by keyboard/__init__.py
init = _setup_name_tables

# List created manually.
keypad_keys = [
    # (scan_code, virtual_key_code, is_extended)
    (126, 194, 0),
    (126, 194, 0),
    (28, 13, 1),
    (28, 13, 1),
    (53, 111, 1),
    (53, 111, 1),
    (55, 106, 0),
    (55, 106, 0),
    (69, 144, 1),
    (69, 144, 1),
    (71, 103, 0),
    (71, 36, 0),
    (72, 104, 0),
    (72, 38, 0),
    (73, 105, 0),
    (73, 33, 0),
    (74, 109, 0),
    (74, 109, 0),
    (75, 100, 0),
    (75, 37, 0),
    (76, 101, 0),
    (76, 12, 0),
    (77, 102, 0),
    (77, 39, 0),
    (78, 107, 0),
    (78, 107, 0),
    (79, 35, 0),
    (79, 97, 0),
    (80, 40, 0),
    (80, 98, 0),
    (81, 34, 0),
    (81, 99, 0),
    (82, 45, 0),
    (82, 96, 0),
    (83, 110, 0),
    (83, 46, 0),
]

shift_is_pressed = False
altgr_is_pressed = False
ignore_next_right_alt = False
shift_vks = set([0x10, 0xA0, 0xA1])

# Modifiers physically held down right now. This mirrors the evdev backend's
# `pressed_modifiers` so that `KeyboardEvent.modifiers` carries the same
# meaning on Windows as it does on Linux/macOS/X11.
modifiers_lock = Lock()
pressed_modifiers = set()

# Win32 spells the two halves of some modifiers inconsistently: the left key
# resolves to the bare name ("Ctrl", "Alt") while the right one keeps its side
# ("Right Ctrl"). `normalize_name` only maps "left menu" to "left alt", so the
# remaining raw spellings are mapped here.
_modifier_name_aliases = {
    "right menu": "right alt",
}

# (scan code, virtual key code, is_extended) for every modifier key, used to
# pick up modifiers that were already held when the hook got installed.
_modifier_key_codes = (
    (0x2A, 0xA0, 0),
    (0x36, 0xA1, 0),
    (0x10, 0x2A, 0),
    (0x1D, 0xA2, 0),
    (0x1D, 0xA3, 1),
    (0x11, 0x1D, 0),
    (0x38, 0xA4, 0),
    (0x38, 0xA5, 1),
    (0x12, 0x38, 0),
    (0x5B, 0x5B, 1),
    (0x5C, 0x5C, 1),
)


def _canonical_modifier_name(name):
    """
    Reduce a key name to the modifier it stands for in the unsided form
    ("shift", "ctrl", "alt", "windows", "alt gr"), or None when `name` is not a
    modifier.

    Collapsing the sides keeps one physical modifier from being tracked as
    both "shift" and "left shift", which would make `down_modifiers` report it
    twice. Note that `alt gr` is kept as-is rather than expanded into
    ctrl+alt; `down_modifiers` collapses it to "alt" either way.
    """
    if not name or not isinstance(name, str):
        return None
    name = normalize_name(name)
    name = _modifier_name_aliases.get(name, name)
    if name not in all_modifiers:
        return None
    for prefix in ("left ", "right "):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    return name if name in all_modifiers else None


def _snapshot_and_update_modifiers(name, event_type):
    """
    Return the modifiers held as of *before* this event, then fold the event
    into `pressed_modifiers`.

    The snapshot is taken first so that a modifier's own key down event does
    not report itself as already held. The evdev backend orders it the same
    way, and `down_modifiers` relies on that ordering to see the modifier
    being pressed.
    """
    modifier = _canonical_modifier_name(name)
    with modifiers_lock:
        snapshot = tuple(sorted(pressed_modifiers))
        if modifier is not None:
            if event_type == KEY_DOWN:
                pressed_modifiers.add(modifier)
            else:
                pressed_modifiers.discard(modifier)
    return snapshot


def _seed_pressed_modifiers():
    """
    Record modifiers that are already down, so that the first events received
    are not reported as unmodified. The evdev backend does the same by reading
    the keys currently held when `listen` starts.
    """
    for scan_code, vk, is_extended in _modifier_key_codes:
        is_down = user32.GetAsyncKeyState(vk) & 0x8000
        if not is_down:
            continue

        entry = (scan_code, vk, is_extended, ())

        # can run before to_name is occupied
        # so go ahead and cache the names if that happens
        # this happens if user calls write before receiving
        # any real key events
        if entry not in to_name:
            to_name[entry] = list(get_event_names(*entry))

        names = to_name[entry]
        modifier = _canonical_modifier_name(names[0] if names else None)
        if modifier is not None:
            with modifiers_lock:
                pressed_modifiers.add(modifier)


# set at the top of prepare_intercept only used for event injection when writing
_event_callback = None


def _dispatch_event(event):
    """
    Single exit point for all keyboard events (real or synthetic).
    """
    if _event_callback is None:
        return True
    return _event_callback(event)


# TODO: this can probably be simplified by making some sort of dedicated class
# that holds the three values

# used to stop the program from injecting events that over take
# actual hardware keypresses so they reach the application first
# this revents a bug in fuzzychips where "th " was expanding to
# "t at " instead of "that "
_hook_release = Condition()
_hook_events_in_flight = 0
# thread identifier
_hook_thread_ident = None


def _enter_hook():
    """
    Called from the hook callback before it handles an event. Blocks
    injections until the matching `_leave_hook`.
    """
    global _hook_thread_ident, _hook_events_in_flight
    _hook_thread_ident = get_ident()
    with _hook_release:
        _hook_events_in_flight += 1


def _leave_hook():
    """
    Called from the hook callback just before it returns to the OS, which is
    when the event is handed over to the application.
    """
    global _hook_events_in_flight
    with _hook_release:
        _hook_events_in_flight -= 1
        if _hook_events_in_flight == 0:
            _hook_release.notify_all()


def _wait_for_hook_release():
    """
    Block until the low-level hook has finished handing its current event to
    the OS, so that injected events cannot overtake it.
    """
    with _hook_release:
        while _hook_events_in_flight > 0:
            if get_ident() == _hook_thread_ident:
                # Called from inside the hook callback itself, which is how
                # remapped and suppressed keys are turned into synthetic
                # events. The callback cannot wait for its own return.
                return
            _hook_release.wait()


def prepare_intercept(callback):
    global _event_callback
    _event_callback = callback
    """
    Registers a Windows low level keyboard hook. The provided callback will
    be invoked for each high-level keyboard event, and is expected to return
    True if the key event should be passed to the next program, or False if
    the event is to be blocked.

    No event is processed until the Windows messages are pumped (see
    start_intercept).
    """
    _setup_name_tables()
    _seed_pressed_modifiers()

    def process_key(event_type, vk, scan_code, is_extended):
        global shift_is_pressed, altgr_is_pressed, ignore_next_right_alt

        # Pressing alt-gr also generates an extra "right alt" event
        if vk == 0xA5 and ignore_next_right_alt:
            ignore_next_right_alt = False
            return True

        modifiers = (
            ("shift",) * shift_is_pressed
            + ("alt gr",) * altgr_is_pressed
            + ("num lock",) * (user32.GetKeyState(0x90) & 1)
            + ("caps lock",) * (user32.GetKeyState(0x14) & 1)
            + ("scroll lock",) * (user32.GetKeyState(0x91) & 1)
        )
        entry = (scan_code, vk, is_extended, modifiers)
        if entry not in to_name:
            to_name[entry] = list(get_event_names(*entry))

        names = to_name[entry]
        name = names[0] if names else None

        # TODO: inaccurate when holding multiple different shifts.
        if vk in shift_vks:
            shift_is_pressed = event_type == KEY_DOWN
        if scan_code == 541 and vk == 162:
            ignore_next_right_alt = True
            altgr_is_pressed = event_type == KEY_DOWN

        # Only the held modifiers; the lock states above pick the character the
        # name resolves to and are deliberately not tracked as modifiers.
        held_modifiers = _snapshot_and_update_modifiers(name, event_type)

        is_keypad = (scan_code, vk, is_extended) in keypad_keys
        return _dispatch_event(
            KeyboardEvent(
                event_type=event_type,
                scan_code=scan_code or -vk,
                name=name,
                is_keypad=is_keypad,
                modifiers=held_modifiers,
            )
        )

    def low_level_keyboard_handler(nCode, wParam, lParam):
        # Physical events are only handed to the target application after this
        # callback returns. Anything injected while it runs would reach the
        # application before the event that triggered it, so keep the hook
        # marked as in flight until the hand-off (see
        # _wait_for_hook_release).
        _enter_hook()
        try:
            try:
                vk = lParam.contents.vk_code
                # LLKHF_INJECTED is set for anything that came out of keybd_event or
                # SendInput, including our own. The old mask (LLKHF_INJECTED | 0x20)
                # only matched injections coming from a lower integrity level, so
                # same-integrity keybd_event events were *not* filtered: every
                # backspace we sent arrived here AND through inject_event(), on two
                # different threads and in no guaranteed order.
                injected = bool(lParam.contents.flags & LLKHF_INJECTED)
                # Determine if this event should be ignored due to synthetic filtering
                ignore_event = (
                    synthetic_mode != WindowsSyntheticModes.REAL
                    and (vk == VK_PACKET or injected)
                )

                if not ignore_event:
                    event_type = KEY_UP if wParam & 0x01 else KEY_DOWN
                    is_extended = lParam.contents.flags & 1

                    if vk == VK_PACKET:
                        # This is text input, not a key
                        inject_event(
                            event_type,
                            name=chr(lParam.contents.scan_code),
                        )
                        return 0
                    scan_code = lParam.contents.scan_code

                    should_continue = process_key(
                        event_type, vk, scan_code, is_extended)
                    if not should_continue:
                        return -1
            except Exception:
                print("Error in keyboard hook:")
                traceback.print_exc()

            return CallNextHookEx(None, nCode, wParam, lParam)
        finally:
            _leave_hook()

    WH_KEYBOARD_LL = c_int(13)
    keyboard_callback = LowLevelKeyboardProc(low_level_keyboard_handler)
    handle = GetModuleHandleW(None)
    thread_id = DWORD(0)
    SetWindowsHookEx(WH_KEYBOARD_LL, keyboard_callback, handle, thread_id)

    # Register to remove the hook when the interpreter exits. Unfortunately a
    # try/finally block doesn't seem to work here.
    atexit.register(UnhookWindowsHookEx, keyboard_callback)


def listen(callback):
    prepare_intercept(callback)
    msg = MSG()
    while GetMessage(ctypes.byref(msg), 0, 0, 0) != 0:
        TranslateMessage(msg)
        DispatchMessage(msg)


def map_name(name):
    _setup_name_tables()

    entries = from_name.get(name)
    if not entries:
        raise ValueError(
            "Key name {} is not mapped to any known key.".format(repr(name))
        )
    for i, entry in entries:
        scan_code, vk, is_extended, modifiers = entry
        yield scan_code or -vk, modifiers


def _send_event(code, event_type):
    # Never overtake the physical event the hook is still handing off.
    _wait_for_hook_release()
    if code == 541:
        # Alt-gr is made of ctrl+alt. Just sending even 541 doesn't do anything.
        user32.keybd_event(0x11, code, event_type, 0)
        user32.keybd_event(0x12, code, event_type, 0)
    elif code > 0:
        vk = scan_code_to_vk.get(code, 0)
        user32.keybd_event(vk, code, event_type, 0)
    else:
        # Negative scan code is a way to indicate we don't have a scan code,
        # and the value actually contains the Virtual key code.
        user32.keybd_event(-code, 0, event_type, 0)


def inject_event(event_type, scan_code=None, name=None, is_keypad=None):
    """
    Injects a synthetic KeyboardEvent directly into listeners,
    bypassing Win32 hooks.
    """

    held_modifiers = _snapshot_and_update_modifiers(name, event_type)

    event = KeyboardEvent(
        event_type=event_type,
        scan_code=scan_code or 0,
        name=name,
        is_keypad=is_keypad,
        device="synthetic",
        modifiers=held_modifiers,
    )
    return _dispatch_event(event)


BACKSPACE_CODE = 14


def _should_inject(code=None):
    return synthetic_mode == WindowsSyntheticModes.FAKE


def _inject(code, event_type):
    name = None
    vk = scan_code_to_vk.get(code)
    if vk in official_virtual_keys:
        name = official_virtual_keys[vk][0]
    inject_event(event_type, scan_code=code, name=name)


def press(code, shiftpressed: bool = False):
    _send_event(code, 0)
    if _should_inject(code):
        _inject(code, KEY_DOWN)


def release(code, shiftpressed: bool = False, notify=True):
    _send_event(code, 2)

    if _should_inject(code):
        _inject(code, KEY_UP)


def grab():
    raise NotImplementedError(
        "grab is not implemneted on windows it's only implemented on the Linux evdev backend")


def ungrab():
    raise NotImplementedError(
        "ungrab is not implemneted on windows it's only implemented on the Linux evdev backend")


def is_grabbed() -> bool:
    return False


def type_unicode(character, notify=True):
    # Never overtake the physical event the hook is still handing off.
    _wait_for_hook_release()
    surrogates = bytearray(character.encode("utf-16le"))
    presses = []
    releases = []

    for i in range(0, len(surrogates), 2):
        higher, lower = surrogates[i: i + 2]

        structure = KEYBDINPUT(
            0,
            (lower << 8) + higher,
            KEYEVENTF_UNICODE,
            0,
            None,
        )
        presses.append(INPUT(INPUT_KEYBOARD, _INPUTunion(ki=structure)))

        structure = KEYBDINPUT(
            0,
            (lower << 8) + higher,
            KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
            0,
            None,
        )
        releases.append(INPUT(INPUT_KEYBOARD, _INPUTunion(ki=structure)))

    inputs = presses + releases
    nInputs = len(inputs)
    LPINPUT = INPUT * nInputs
    pInputs = LPINPUT(*inputs)
    cbSize = c_int(ctypes.sizeof(INPUT))
    SendInput(nInputs, pInputs, cbSize)

    # --- Inject synthetic logical events ---
    # logical event has no code
    if _should_inject(code=0):
        # no scancodes for unicode events as they could be multiple codes long
        inject_event(KEY_DOWN, name=character)
        inject_event(KEY_UP, name=character)


if __name__ == "__main__":
    _setup_name_tables()
    import pprint

    pprint.pprint(to_name)
    pprint.pprint(from_name)
    # listen(lambda e: print(e.to_json()) or True)
