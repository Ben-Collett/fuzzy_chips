import keyboard
from config import current_config
from buffer import RingBuffer
from frozen_dict import FrozenDict
from utils import backspaces_to_delete_previous_word, shift_press_release
from utils import down_modifiers, to_utf
from command_processor import CommandProcessor
from commands import make_processor
from collection_utils import count_where, captlize
from casing import Casing
import threading
import sys
import os
from modifiers import SHIFT, CTRL, ALT, WINDOWS

keyboard.init(
    linux_collision_safety_mode=keyboard.LinuxCollisionSafetyModes.PATIENT)

stop_event = threading.Event()
current_casing = Casing.NORMAL
expected_counter = 0
_buffer = RingBuffer(100)


def normal_casing():
    return current_casing == Casing.NORMAL


def kebab_casing():
    return current_casing == Casing.KEBAB


def _terminate(*args):
    print("terminating...")
    stop_event.set()


def clear_buffer(*args):
    _buffer.clear()


def write(text: str | list[str]):
    if isinstance(text, str):
        keyboard.write(text)
    else:
        for key in text:
            if command_processor.has_command(key):
                command_processor.process(key)
            else:
                keyboard.press_and_release(key)


def _backspace(n_times):
    for _ in range(0, n_times):
        keyboard.press_and_release("backspace")


def _is_arrow(name: str):
    arrows = ["left", "right", "up", "down"]
    return name in arrows


# TODO: THIS IS A HACK UNTIL I SOLVE AT A LOWER LEVEL
# ALSO I WILL NEED TO KEEP TRACK OF LEFT AND RIGHT VERSIONS NOT BOTH AT ONCE
def _is_shift(name: str):
    return "shift" in name.lower()


def _is_ctrl(name: str):
    return "ctrl" in name.lower()


def _is_alt(name: str):
    return "alt" in name.lower()


def _is_meta(name: str):
    return "windows" in name.lower()


just_pressed_shift: bool = False
prev_real_event: keyboard.KeyboardEvent = None


def determine_amount_to_backspace_shift_backspace(buffer: list[str]):
    return backspaces_to_delete_previous_word(buffer)


def _is_not_a_command(command: str):
    return not command_processor.has_command(command)


def _non_command_count(to_write: list[str]):
    return count_where(_is_not_a_command, to_write)


def backspace_then_write(backspace_count, to_write, update_expected=True):
    if update_expected:
        global expected_counter
        if isinstance(to_write, list):
            expected_counter = backspace_count + _non_command_count(to_write)
        else:
            expected_counter = backspace_count + len(to_write)
    _backspace(backspace_count)
    write(to_write)


def prev_word_toggle_prev(*args):
    print(expected_counter)


def restart(_):
    print("restarting")
    os.execv(sys.executable, [sys.executable] + sys.argv)


def delete_previous_word(* args):
    global expected_counter
    buffer = _buffer.get()
    _buffer.backspace()

    expected_counter = determine_amount_to_backspace_shift_backspace(
        buffer)

    _backspace(expected_counter)


def toggle_casing(casing):
    global current_casing
    current_casing = Casing.NORMAL if current_casing == casing else casing


def toggle_kebab_case(*args):
    toggle_casing(Casing.KEBAB)


# command processor logic
command_processor: CommandProcessor = make_processor()
command_processor.register("quit", _terminate)
command_processor.register("restart", restart)
command_processor.register("clear_buffer", clear_buffer)

# effects previous word
command_processor.register("prev_word_toggle_case", prev_word_toggle_prev)
command_processor.register("prev_word_upper_case", _terminate)
command_processor.register("prev_word_lower_case", _terminate)
command_processor.register("full_prev_word_all_caps", _terminate)
command_processor.register("full_prev_word_all_lower", _terminate)

# casing
command_processor.register("toggle-kebab-case", toggle_kebab_case)
command_processor.register("snake_mode", _terminate)
command_processor.register("proper_mode", _terminate)
command_processor.register("cammel_mode", _terminate)
command_processor.register("upper_snake", _terminate)


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
            backspace_then_write(back_count, to_write,
                                 update_expected=True)
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
    should_clear = name in clear_on

    if "windows_down" in clear_on:
        should_clear = should_clear or meta_down
    if "alt_down" in clear_on:
        should_clear = should_clear or alt_down
    if "ctrl_down" in clear_on:
        should_clear = should_clear or ctrl_down

    if should_clear:
        clear_buffer()
        return True
    return False


def add_utf_and_update_expected(utf: str):
    global expected_counter
    if utf is not None and (utf.isprintable() or utf.isspace()):
        if expected_counter > 0:
            expected_counter -= 1
        _buffer.add(utf)


def handle_space_punctuation(word, append_chars, white_space, prev_whitespace):
    PUNCTUATION_PLUS_SPACE = 2
    at_start_of_buffer = len(_buffer) <= PUNCTUATION_PLUS_SPACE
    # append punctuation when spacing
    if word in append_chars and len(white_space) == 1 and not at_start_of_buffer:
        to_write = word + prev_whitespace
        backspace_count = len(prev_whitespace) + len(word) + 1
        backspace_then_write(backspace_count, to_write,
                             update_expected=True)
        return True
    return False


def captlize_if_needed(to_write, to_write_is_str, config):
    capitalize_after = config.capitalize_after
    captlize_passthrough = config.capitalize_passthrough

    should_capitalize = _buffer.should_captlize_prev_word(
        captilize_after=capitalize_after, pass_through=captlize_passthrough) and to_write_is_str
    if should_capitalize:
        return captlize(to_write)
    return to_write


def start_overlap_length(s1: str, s2: str):
    length = 0
    short_length = min(len(s1), len(s2))
    for i in range(0, short_length):
        if s1[i] != s2[i]:
            break
        length += 1
    return length


def handle_space(event: keyboard.KeyboardEvent, shift_down, config):
    global expected_counter
    chip_map = config.chip_map
    append_chars = config.append_chars
    is_space = event.name == "space"
    pressed_key = event.event_type == keyboard.KEY_DOWN
    typing = expected_counter > 0

    if is_space and pressed_key and not shift_down and not typing:
        process_chip = True
        _buffer.add(' ')
        prev_whitespace = _buffer.get_white_space_before_prev_word()
        white_space = _buffer.get_trailing_white_space()
        word = _buffer.get_prev_word()

        if handle_space_punctuation(word, append_chars, white_space, prev_whitespace):
            return True

        # only wan to expan chip if there is only 1 ' '
        if len(white_space) > 1:
            return process_chip

        char_frequency = FrozenDict.from_string(word)
        to_write = ""

        if process_chip and char_frequency in chip_map.keys():
            to_write = chip_map[char_frequency]
        else:
            to_write = word

        to_write_is_str = isinstance(to_write, str)
        to_write = captlize_if_needed(to_write,  to_write_is_str, config)

        if to_write != "" and to_write != word:
            overlapping_start = start_overlap_length(
                to_write, word) if to_write_is_str else 0

            to_write = to_write[overlapping_start:]
            to_backspace_count = len(word)+1-overlapping_start

            if to_write_is_str:
                to_write += " "
            backspace_then_write(to_backspace_count,
                                 to_write, update_expected=True)

            return True
        # backspace space if not writing
        _buffer.backspace()
    return False


def _process_event(event: keyboard.KeyboardEvent, config=current_config):
    global prev_real_event
    global _buffer
    global expected_counter, typing

    if handle_auto_append(event, config):
        return

    # print(event.name)
    # print(_buffer)
    # print("------------------------------------------------")

    # handle_auto_append, returns true if should early return

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

    if handle_space(event, shift_down, config):
        return

    utf: str = to_utf(event, shift_down)
    add_utf_and_update_expected(utf)


def process_event_wrapper(event):
    global prev_real_event
    _process_event(event)
    if expected_counter == 0:
        prev_real_event = event


def main():
    keyboard.hook(process_event_wrapper)
    try:
        stop_event.wait()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
