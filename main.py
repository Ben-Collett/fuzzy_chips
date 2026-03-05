from modifiers import SHIFT, CTRL, ALT, WINDOWS
import os
import sys
import threading
from casing import Casing, convert_casing
from collection_utils import count_where, captlize, is_not_empty_str
from ipc_server import IPCServer
from commands import make_processor
from command_processor import CommandProcessor
from utils import down_modifiers, to_utf, is_str
from utils import backspaces_to_delete_previous_word, shift_press_release
from frozen_dict import FrozenDict
from threading import Event
from buffer import RingBuffer
from config import current_config, Config
import keyboard

keyboard.init(
    linux_collision_safety_mode=keyboard.LinuxCollisionSafetyModes.PATIENT)

stop_event = threading.Event()
current_casing = Casing.NORMAL
expected_counter = 0
_buffer = RingBuffer(100)
_right_arrow_buffer = RingBuffer(100)
just_set = Event()


def activate_casing(casing):
    global current_casing
    current_casing = casing


def _terminate(*args):
    print("terminating...")
    stop_event.set()


def clear_buffer(*args):
    _buffer.clear()
    _right_arrow_buffer.clear()


def move_last(source: RingBuffer, target: RingBuffer):
    if not source.is_empty():
        target.add(source.backspace())


def set_buffer(args, buffer):
    just_set.set()
    buffer.set_buffer(args)


def set_main_buffer(args):
    set_buffer(args, _buffer)


def set_buffer_right(args):
    set_buffer(args[::-1], _right_arrow_buffer)


def write(text: str | list[str]):
    if is_str(text) and len(text) > 0:
        keyboard.write(text)
    else:
        for key in text:
            command = key.split(" ")[0]
            if command_processor.has_command(command):
                command_processor.process(key)
            else:
                keyboard.press_and_release(key)


def backspace(n_times):
    for _ in range(0, n_times):
        keyboard.press_and_release("backspace")


prev_real_event: keyboard.KeyboardEvent | None = None


def determine_amount_to_backspace_shift_backspace(buffer: list[str]) -> int:
    return backspaces_to_delete_previous_word(buffer)


def _is_not_a_command(command: str):
    return not command_processor.has_command(command)


def _non_command_count(to_write: list[str]):
    return count_where(_is_not_a_command, to_write)


def backspace_then_write(backspace_count, to_write, update_expected=True):
    if update_expected:
        global expected_counter
        if is_str(to_write):
            expected_counter = backspace_count + len(to_write)
        else:
            expected_counter = backspace_count + _non_command_count(to_write)
    backspace(backspace_count)
    write(to_write)


def restart(_):
    print("restarting")
    os.execv(sys.executable, [sys.executable] + sys.argv)


def delete_previous_word(*args):
    global expected_counter
    buffer = _buffer.get()
    _buffer.backspace()

    back_count = determine_amount_to_backspace_shift_backspace(buffer)
    to_write = ""
    if current_casing.is_not_normal_casing and len(buffer) - back_count - len(_buffer.get_leading_white_space()) > 1:
        to_write = " "
    backspace_then_write(back_count, to_write, update_expected=True)


def activate_kabab_mode(*args):
    activate_casing(Casing.KEBAB)


def activate_snake_mode(*args):
    activate_casing(Casing.SNAKE)


def activate_normal_casing_mode(*args):
    activate_casing(Casing.NORMAL)


def activate_upper_snake_mode(*args):
    activate_casing(Casing.UPPER_SNAKE)


def activate_proper_mode(*args):
    activate_casing(Casing.PROPER)


def activate_camel_mode(*args):
    activate_casing(Casing.CAMEL)


# command processor logic
command_processor: CommandProcessor = make_processor()
ipc_enabled = []
command_processor.register("restart", restart)

command_processor.register("quit", _terminate)

commands = {
    "clear_buffer": clear_buffer,
    "normalc": activate_normal_casing_mode,
    "kebab-case-mode": activate_kabab_mode,
    "snake_case_mode": activate_snake_mode,
    "ProperCaseMode": activate_proper_mode,
    "camelCaseMode": activate_camel_mode,
    "UPPER_SNAKE_CASE_MODE": activate_upper_snake_mode,
    "cb": clear_buffer,
    "mc": activate_normal_casing_mode,
    "sc": activate_snake_mode,
    "pm": activate_proper_mode,
    "cm": activate_camel_mode,
    "us": activate_upper_snake_mode,
    "kb": activate_kabab_mode,
    # WARNING: ONLY WORKS WITH IPC UNLESS YOU PAD THE NEW BUFFER WITH JUNK DATA TO MAKE UP FOR BACSPACES
    "sm": set_main_buffer,
    "sr": set_buffer_right,
}


def update_ipc_enabled(config=current_config):
    command_processor.ipc_commands.clear()
    for command in commands.keys():
        if command in config.ipc_enabled_commands:
            command_processor.ipc_commands.add(command)


for command, func in commands.items():
    command_processor.register(command, func)
update_ipc_enabled()


def handle_auto_append(event, config):
    name = event.name
    auto_append = config.auto_apped
    append_chars = config.append_chars
    if auto_append and name in append_chars:
        leading_whitespace = _buffer.get_trailing_white_space()
        if len(leading_whitespace) > 0:
            _buffer.add(name)
            backspace_count = len(leading_whitespace) + 1
            to_write = name + leading_whitespace
            backspace_then_write(backspace_count, to_write,
                                 update_expected=True)

            return True
    return False


def handle_if_release_event(event: keyboard.KeyboardEvent, toggle_case_on):
    released_key = event.event_type == keyboard.KEY_UP
    name = event.name
    if released_key:
        name_equals_prev = prev_real_event and prev_real_event.name == name
        manual_typing = expected_counter == 0
        if name_equals_prev and name in toggle_case_on and manual_typing:
            back_count, to_write = shift_press_release(_buffer.get())
            backspace_then_write(back_count, to_write, update_expected=True)
        return True
    return False


def handle_backspace(event, shift_down):
    global expected_counter
    is_backspace = event.name == "backspace"
    pressed_key = event.event_type == keyboard.KEY_DOWN
    if shift_down and is_backspace and pressed_key and expected_counter == 0:
        delete_previous_word()
        return True
    elif is_backspace and pressed_key:
        _buffer.backspace()
        if expected_counter > 0:
            expected_counter -= 1
        return True
    return False


def handle_clear(name, config, meta_down, ctrl_down, alt_down):
    clear_on = current_config.clear_buffer_on_keys
    safe_clear = current_config.just_set_safe_clear
    should_clear = name in clear_on

    if "windows_down" in clear_on:
        should_clear = should_clear or meta_down
    if "alt_down" in clear_on:
        should_clear = should_clear or alt_down
    if "ctrl_down" in clear_on:
        should_clear = should_clear or ctrl_down
    if not just_set.is_set() and name in safe_clear:
        should_clear = True

    if should_clear:
        clear_buffer()
        return True
    return False


def add_utf_and_update_expected(utf: str | None):
    global expected_counter
    if utf is not None and (utf.isprintable() or utf.isspace()):
        if expected_counter > 0:
            expected_counter -= 1
        _buffer.add(utf)


def handle_space_punctuation(word, append_chars, white_space, prev_whitespace):
    PUNCTUATION_PLUS_SPACE = 2
    at_start_of_buffer = len(_buffer) <= PUNCTUATION_PLUS_SPACE
    space_length = len(white_space)
    # append punctuation when spacing
    if word in append_chars and space_length == 1 and not at_start_of_buffer:
        to_write = word + prev_whitespace
        backspace_count = len(prev_whitespace) + len(word) + 1
        backspace_then_write(backspace_count, to_write, update_expected=True)
        return True
    return False


def captlize_if_needed(to_write, to_write_is_str, config):
    capitalize_after = config.capitalize_after
    captlize_passthrough = config.capitalize_passthrough

    should_capitalize = (
        current_casing.is_normal_casing
        and _buffer.should_captlize_prev_word(
            captilize_after=capitalize_after, pass_through=captlize_passthrough
        )
        and to_write_is_str
    )
    if should_capitalize:
        return captlize(to_write)
    return to_write


def valid_chip(freq, config=current_config):
    return freq in current_config.chip_map.keys()


# TODO: this name kind of sucks
def extract_ignored_leading_word_trailing(word: str, config=current_config):
    ignored_leading = current_config.ignored_leading
    ignored_trailing = current_config.ignored_trailing

    leading = []
    trailing = []
    for ch in word:
        if ch in ignored_leading:
            leading.append(ch)
        else:
            break
    for ch in reversed(word):
        if ch in ignored_trailing:
            trailing.append(ch)
        else:
            break

    leading_str = "".join(leading)
    trailing_str = "".join(reversed(trailing))
    word = word.removeprefix(leading_str).removesuffix(trailing_str)
    return leading_str, word, trailing_str


def escape_to_normal_casing(white_space):

    # this approach means if a user hits space then clears the buffer and hits space again it won't restore normal mode
    if current_casing.is_not_normal_casing and white_space == "  ":
        activate_normal_casing_mode()
        backspace(1)
        return True
    return False


# updates the captlization based on upper_count, 1 = catplize, 1>uppercase, else no change
def _update_captlization(word, upper_count: int):
    if not is_str(word):
        return word
    if upper_count == 1:
        word = captlize(word)
    elif upper_count > 1:
        word = word.upper()
    return word


def _get_chip_result(word, config: Config) -> list[str] | str | None:
    chip_map = config.chip_map
    char_frequency = FrozenDict.from_string(word)

    if valid_chip(char_frequency, config):
        return chip_map[char_frequency]

    def is_upper(ch): return ch.isupper()
    upper_count = count_where(is_upper, word)
    word = word.lower()
    char_frequency = FrozenDict.from_string(word)
    is_valid_chip = valid_chip(char_frequency, config)
    if is_valid_chip:
        chip = chip_map[char_frequency]
        return _update_captlization(chip, upper_count)

    leading, w, trailing = extract_ignored_leading_word_trailing(
        word, config)
    char_frequency = FrozenDict.from_string(w)

    # we check if it's a str because if it is a list we don't handle ignoring leading and trailing
    # and if it got to this point we know it wasn't an exact match for a command chip
    is_valid_chip = valid_chip(char_frequency, config) and is_str(
        chip_map[char_frequency])
    if is_valid_chip:
        chip = chip_map[char_frequency]
        return leading+_update_captlization(chip, upper_count)+trailing
    return None


def handle_space(event: keyboard.KeyboardEvent, shift_down, config):
    global expected_counter
    append_chars = config.append_chars
    is_space = event.name == "space"
    pressed_key = event.event_type == keyboard.KEY_DOWN
    typing = expected_counter > 0

    if is_space and pressed_key and not typing:
        _buffer.add(" ")
        white_space = _buffer.get_trailing_white_space()
        # escapes snake or camel casing and what not
        if escape_to_normal_casing(white_space):
            return True

        prev_whitespace = _buffer.get_white_space_before_prev_word()
        word = _buffer.get_prev_word()
        prev_word = _buffer.get_word(-2)

        # handle appending punctuation at end of previous word
        if not shift_down and handle_space_punctuation(
            word, append_chars, white_space, prev_whitespace
        ):
            return True

        # only want to expand chip if there is only 1 ' '
        process_chip = not shift_down and len(white_space) == 1

        to_write = None
        if process_chip:
            # can output none
            to_write = _get_chip_result(word, config)

        if to_write is None:
            to_write = word

        to_write_is_str = is_str(to_write)
        to_write = captlize_if_needed(to_write, to_write_is_str, config)
        # buffer_length = len(_buffer)

        overlapping_start = 0
        prepended = 0

        if to_write_is_str:
            to_write, prepended, overlapping_start = convert_casing(
                to_write, word, prev_word, prev_whitespace, current_casing
            )

        if is_not_empty_str(to_write) and (to_write != word or prepended != 0):
            to_write = to_write[overlapping_start:]
            to_backspace_count = len(word) + 1 - overlapping_start + prepended
            if to_write_is_str:
                to_write += " "
            backspace_then_write(to_backspace_count,
                                 to_write, update_expected=True)
        return True
    return False


def _process_event(event: keyboard.KeyboardEvent, config=current_config):
    global prev_real_event
    global _buffer, _right_arrow_buffer
    global expected_counter, typing

    if handle_auto_append(event, config):
        return

    down_mods = down_modifiers(event)
    shift_down = SHIFT in down_mods
    alt_down = ALT in down_mods
    meta_down = WINDOWS in down_mods
    ctrl_down = CTRL in down_mods

    if handle_clear(event.name, config, meta_down, ctrl_down, alt_down):
        return

    if handle_backspace(event, shift_down):
        return

    if handle_if_release_event(event, config.toggle_case_on):
        return

    # ============= EVENT GUARANTEED BE DOWN PAST THIS POINT ================

    if handle_space(event, shift_down, config):
        return

    name = event.name
    if name == "left":
        move_last(source=_buffer, target=_right_arrow_buffer)
        return
    elif name == "right":
        move_last(source=_right_arrow_buffer, target=_buffer)
        return
    elif name == "delete":
        _right_arrow_buffer.remove_first()
        return

    utf: str | None = to_utf(event, shift_down)
    add_utf_and_update_expected(utf)


def process_event_wrapper(event):
    global prev_real_event
    _process_event(event)
    just_set.clear()
    if expected_counter == 0:
        prev_real_event = event


def main():
    # Start IPC server
    ipc_server = IPCServer(command_processor)
    ipc_server.start()

    keyboard.hook(process_event_wrapper)
    try:
        stop_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        ipc_server.stop()


if __name__ == "__main__":
    main()
