import keyboard
import get_chips
from buffer import RingBuffer
from frozen_dict import FrozenDict

keyboard.patient_collision_safe_mode()
_chip_map = get_chips.chip_map()
_buffer = RingBuffer(100)

append_chars = [".", ",", "!", "?"]
auto_append = False
captlize_after = [".", "!", "?"]

expected_counter = 0
punct_expected_counter = 0


def _toggle_capitlization(s: str):
    if len(s) == 0:
        return ""
    if s[0].islower():
        return s[0].upper() + s[1:]
    return s[0].lower() + s[1:]


def write(text: str):
    keyboard.write(text)


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
    expected_counter = len(prev_word) + 2*len(white_space)
    _backspace(len(prev_word)+len(white_space))
    write(to_write)


just_pressed_shift: bool = False

shift_down = False
ctrl_down = False
alt_down = False
meta_down = False


def _process_event(event: keyboard.KeyboardEvent):
    global just_pressed_shift
    global alt_down, ctrl_down, shift_down, alt_down, meta_down
    global _buffer
    global expected_counter, punct_expected_counter, _typing

    name: str = event.name

    if auto_append and name in append_chars:
        leading_whitespace = _buffer.get_trailing_white_space()
        if len(leading_whitespace) > 0:
            _buffer.add(name)
            _backspace(len(leading_whitespace)+1)
            write(name)
            write(leading_whitespace)
            # + one for the name and the other
            punct_expected_counter = len(leading_whitespace) + 2
            return
    pressed_key = event.event_type == keyboard.KEY_DOWN
    released_key = not pressed_key
    is_shift = _is_shift(name)
    is_ctrl = _is_ctrl(name)
    is_meta = _is_meta(name)
    is_alt = _is_alt(name)
    is_backspace = name == "backspace"

    if is_backspace and pressed_key:
        _buffer.backspace()
        return

    if is_shift and pressed_key:
        shift_down = True
        just_pressed_shift = True
    elif is_shift and released_key:
        shift_down = False
        if just_pressed_shift:
            just_pressed_shift = False
            _toggle_prev()
    else:
        just_pressed_shift = False

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
    if is_space and released_key and not shift_down and not _typing:
        process_chip = True
        white_space = _buffer.get_trailing_white_space()
        prev_whitespace = _buffer.get_white_space_before_prev_word()
        word = _buffer.get_prev_word()

        # append punctuation when spacing
        if word in append_chars and punct_expected_counter == 0 and len(white_space) == 1:
            punct_expected_counter = len(prev_whitespace) + len(word) + 1
            _backspace(punct_expected_counter)
            write(word+prev_whitespace)
            return
        # I don't want to process as chip unless there was exactly one ' '
        if white_space != ' ':
            process_chip = False
        char_frequency = FrozenDict.from_string(word)
        to_write = ""

        if process_chip and char_frequency in _chip_map.keys():
            to_write = _chip_map[char_frequency]

        should_capitalize = punct_expected_counter == 0 and _buffer.should_captlize_prev_word(
            captilize_after=captlize_after)
        if should_capitalize:
            if to_write == "":
                to_write = word.capitalize()
            else:
                to_write = to_write.capitalize()

        if to_write != "" and to_write != word:
            _backspace(len(word)+1)
            expected_counter = len(to_write)+2
            write(to_write)
            write(" ")

    if released_key:
        return
    if meta_down or _is_arrow(name):
        _buffer.clear()
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
        if punct_expected_counter > 0:
            punct_expected_counter -= 1
        _buffer.add(utf)


def main():
    keyboard.hook(_process_event)
    keyboard.wait()


if __name__ == "__main__":
    main()
