import keyboard
from config import current_config
from buffer import RingBuffer
from frozen_dict import FrozenDict
from utils import backspaces_to_delete_previous_word
from command_processor import CommandProcessor
from commands import make_processor
import threading

stop_event = threading.Event()


def _terminate(_):
    stop_event.set()


command_processor: CommandProcessor = make_processor()
command_processor.register("quit", _terminate)


def is_empty(iterable):
    return len(iterable) == 0


keyboard.patient_collision_safe_mode()
_buffer = RingBuffer(100)


expected_counter = 0


def _toggle_capitlization(s: str):
    if len(s) == 0:
        return ""
    if s[0].islower():
        return s[0].upper() + s[1:]
    return s[0].lower() + s[1:]


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


def _toggle_prev():
    global expected_counter
    prev_word = _buffer.get_prev_word()
    white_space = _buffer.get_trailing_white_space()
    to_write = f'{_toggle_capitlization(prev_word)}{white_space}'
    backspace_count = len(prev_word)+len(white_space)
    backspace_then_write(backspace_count, to_write, update_expected=True)


just_pressed_shift: bool = False
prev_real_event: keyboard.KeyboardEvent = None


def _before_return_hook(event):
    global expected_counter
    global prev_real_event
    if expected_counter == 0:
        prev_real_event = event


def determine_amount_to_backspace_shift_backspace(buffer: list[str]):
    return backspaces_to_delete_previous_word(buffer)


shift_down = False
ctrl_down = False
alt_down = False
meta_down = False


def backspace_then_write(backspace_count, to_write, update_expected=True):
    if update_expected:
        global expected_counter
        expected_counter = backspace_count + len(to_write)
    _backspace(backspace_count)
    write(to_write)


def _process_event(event: keyboard.KeyboardEvent, config=current_config):
    global prev_real_event
    global alt_down, ctrl_down, shift_down, alt_down, meta_down
    global _buffer
    global expected_counter, _typing

    chip_map = config.chip_map
    append_chars = config.append_chars
    auto_append = config.auto_apped
    capitalize_after = config.capitalize_after

    name: str = event.name
    # print(name)
    # print(_buffer)
    # print("------------------------------------------------")
    if auto_append and name in append_chars:
        leading_whitespace = _buffer.get_trailing_white_space()
        if len(leading_whitespace) > 0:
            _buffer.add(name)
            backspace_count = len(leading_whitespace) + 1
            to_write = name + leading_whitespace
            backspace_then_write(backspace_count, to_write,
                                 update_expected=True)

            _before_return_hook(event)
            return
    pressed_key = event.event_type == keyboard.KEY_DOWN
    released_key = not pressed_key
    is_shift = _is_shift(name)
    is_ctrl = _is_ctrl(name)
    is_meta = _is_meta(name)
    is_alt = _is_alt(name)
    is_backspace = name == "backspace"

    if shift_down and is_backspace and pressed_key and expected_counter == 0:
        buffer = _buffer.get()
        _buffer.backspace()

        expected_counter = determine_amount_to_backspace_shift_backspace(
            buffer)

        _backspace(expected_counter)

    elif is_backspace and pressed_key:
        _buffer.backspace()
        if expected_counter > 0:
            expected_counter -= 1
        _before_return_hook(event)
        return

    if is_shift and pressed_key:
        shift_down = True
    elif is_shift and released_key:
        shift_down = False

    if is_ctrl and pressed_key:
        ctrl_down = True
    elif is_ctrl and released_key:
        ctrl_down = False

    if is_alt and pressed_key:
        alt_down = True
    elif is_alt and released_key:
        alt_down = False

    if is_meta and pressed_key:
        meta_down = True
    elif is_meta and released_key:
        meta_down = False

    is_space = name == "space"
    _typing = expected_counter > 0
    if is_space and pressed_key and not shift_down and not _typing:
        process_chip = True
        _buffer.add(' ')
        white_space = _buffer.get_trailing_white_space()
        prev_whitespace = _buffer.get_white_space_before_prev_word()
        word = _buffer.get_prev_word()

        PUNCTUATION_PLUS_SPACE = 2
        at_start_of_buffer = len(_buffer) <= PUNCTUATION_PLUS_SPACE
        # append punctuation when spacing
        if word in append_chars and len(white_space) == 1 and not at_start_of_buffer:
            to_write = word + prev_whitespace
            backspace_count = len(prev_whitespace) + len(word) + 1
            backspace_then_write(backspace_count, to_write,
                                 update_expected=True)
            _before_return_hook(event)
            return
        # I don't want to process as chip unless there was exactly one ' '
        if white_space != ' ':
            process_chip = False
        char_frequency = FrozenDict.from_string(word)
        to_write = ""

        if process_chip and char_frequency in chip_map.keys():
            to_write = chip_map[char_frequency]

        to_write_is_str = isinstance(to_write, str)
        should_capitalize = _buffer.should_captlize_prev_word(
            captilize_after=capitalize_after) and to_write_is_str
        if should_capitalize:
            if to_write == "":
                to_write = word.capitalize()
            else:
                to_write = to_write.capitalize()

        if to_write != "" and to_write != word:
            overlapping_start = 0
            if to_write_is_str:
                for i in range(min(len(to_write), len(word))):
                    if to_write[i] != word[i]:
                        break
                    overlapping_start += 1

            to_write = to_write[overlapping_start:]
            to_backspace_count = len(word)+1-overlapping_start

            # additional space if chip is a string
            if to_write_is_str:
                to_write += " "
            backspace_then_write(to_backspace_count,
                                 to_write, update_expected=True)

            _before_return_hook(event)
            return
        # backspace space if not writing
        _buffer.backspace()

    if released_key:
        name_equals_prev = prev_real_event and prev_real_event.name == name
        manual_typing = expected_counter == 0
        if name_equals_prev and name in current_config.toggle_case_on and manual_typing:
            _toggle_prev()
        _before_return_hook(event)
        return
    clear_on = current_config.clear_buffer_on_keys
    should_clear = name in clear_on

    if "windows_down" in clear_on:
        should_clear = should_clear or meta_down
    if "alt_down" in clear_on:
        should_clear = should_clear or alt_down
    if "ctrl_down" in clear_on:
        should_clear = should_clear or ctrl_down

    if should_clear:
        _buffer.clear()

        _before_return_hook(event)
        return

    utf: str = None
    if len(name) == 1:
        if shift_down:
            utf = name.upper()
        else:
            utf = name
    elif name == "space":
        utf = " "

    if utf is not None and (utf.isprintable() or utf.isspace()):
        if expected_counter > 0:
            expected_counter -= 1
        _buffer.add(utf)
    _before_return_hook(event)


def main():
    keyboard.hook(_process_event)
    stop_event.wait()


if __name__ == "__main__":
    main()
