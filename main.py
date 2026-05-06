from modifiers import SHIFT, CTRL, ALT, WINDOWS
from casing import Casing, convert_casing
from spacing_type import SpacingType
from collection_utils import count_where, captlize, is_not_empty_str
from ipc_server import IPCServer
from utils import down_modifiers, to_utf, is_str
from utils import backspaces_to_delete_previous_word
from buffer import KeyBuffer
from config import Config
from expansion_utils import expand_chunking, get_chip_result, shift_press_release
from expansion_utils import expand_code_casing, is_valid_chip_str, determine_code_casing
from expansion_utils import expand_new
from utils import is_all_non_alphanumeric_str
import keyboard
import signal

from main_context import AppContext
from commands import clear_buffer, activate_normal_casing_mode, terminate


def move_last(source: KeyBuffer, target: KeyBuffer):
    if not source.is_empty():
        target.add_entry(source.backspace_entry())


def set_buffer(args, buffer):
    ctx = AppContext.get_current()
    ctx.just_set.set()

    if not buffer.is_equal(args):
        buffer.set_buffer(args, recent=False)


def set_main_buffer(args: list[str]):
    set_buffer(args, AppContext.get_current()._buffer)


def set_buffer_right(args: list[str]):
    set_buffer(args[::-1], AppContext.get_current()._right_arrow_buffer)


def write(text: str | list[str]):
    ctx = AppContext.get_current()
    if is_str(text) and len(text) > 0:
        keyboard.write(text)
    else:
        for key in text:
            command = key.split(" ")[0]
            if ctx.command_processor.has_command(command):
                ctx.command_processor.process(key)
            else:
                keyboard.write_list([key])


def backspace(n_times):
    for _ in range(0, n_times):
        keyboard.press_and_release("backspace")


def decrement_expected_counter():
    ctx = AppContext.get_current()
    if ctx.expected_counter > 0:
        ctx.expected_counter -= 1


def determine_amount_to_backspace_shift_backspace(buffer: list[str]) -> int:
    return backspaces_to_delete_previous_word(buffer)


def _is_not_a_command(command: str):
    ctx = AppContext.get_current()
    return not ctx.command_processor.has_command(command)


def _non_command_count(to_write: list[str]):
    return count_where(_is_not_a_command, to_write)


def backspace_then_write(backspace_count, to_write, update_expected=True):
    ctx = AppContext.get_current()
    if update_expected:
        if is_str(to_write):
            ctx.expected_counter = backspace_count + len(to_write)
        else:
            ctx.expected_counter = backspace_count + \
                _non_command_count(to_write)
    backspace(backspace_count)
    write(to_write)


def delete_previous_word(_: list[str]):
    ctx = AppContext.get_current()
    buffer = ctx._buffer.get()

    ctx._buffer.backspace()

    back_count = max(
        determine_amount_to_backspace_shift_backspace(buffer) - 1, 0)
    to_write = ""
    if (
        ctx.current_casing.is_not_normal_casing
        and len(buffer) - back_count - len(ctx._buffer.get_leading_white_space()) > 1
    ):
        to_write = " "
    backspace_then_write(back_count, to_write, update_expected=True)


def handle_auto_append(event, config: Config):
    name = event.name
    auto_append = config.general.auto_append
    append_chars = config.general.append_chars
    ctx = AppContext.get_current()
    if auto_append and name in append_chars:
        leading_whitespace = ctx._buffer.get_trailing_white_space()
        if len(leading_whitespace) > 0:
            ctx._buffer.add(name)
            backspace_count = len(leading_whitespace) + 1
            to_write = name + leading_whitespace
            backspace_then_write(backspace_count, to_write,
                                 update_expected=True)

            return True
    return False


def handle_if_release_event(event: keyboard.KeyboardEvent, toggle_case_on):
    ctx = AppContext.get_current()
    released_key = event.event_type == keyboard.KEY_UP
    name = event.name
    if released_key:
        name_equals_prev = ctx.prev_real_event and ctx.prev_real_event.name == name
        manual_typing = ctx.expected_counter == 0
        if name_equals_prev and name in toggle_case_on and manual_typing:
            word = ctx._buffer.get_last_word()
            white_space = ctx._buffer.get_trailing_white_space()

            back_count, to_write = shift_press_release(word, white_space)
            backspace_then_write(back_count, to_write, update_expected=True)
        return True
    return False


def handle_backspace(event, shift_down):
    ctx = AppContext.get_current()
    is_backspace = event.name == "backspace"
    pressed_key = event.event_type == keyboard.KEY_DOWN
    if is_backspace and pressed_key:
        if shift_down and ctx.expected_counter == 0:
            delete_previous_word([])
        else:
            ctx._buffer.backspace()
            decrement_expected_counter()
        return True
    return False


def handle_clear(name, config: Config, meta_down: bool, ctrl_down: bool, alt_down: bool):
    ctx = AppContext.get_current()
    clear_on: list[str] = config.general.clear_buffer_on
    safe_clear = config.rare.just_set_safe_clear
    should_clear = name in clear_on

    if "windows_down" in clear_on:
        should_clear = should_clear or meta_down
    if "alt_down" in clear_on:
        should_clear = should_clear or alt_down
    if "ctrl_down" in clear_on:
        should_clear = should_clear or ctrl_down
    if not ctx.just_set.is_set() and name in safe_clear:
        should_clear = True

    if should_clear:
        clear_buffer([])
        return True
    return False


def add_utf_and_update_expected(utf: str | None):
    ctx = AppContext.get_current()
    if utf is not None and (utf.isprintable() or utf.isspace()):
        ctx._buffer.add(utf, recent=ctx.expected_counter == 0)
        decrement_expected_counter()


def handle_space_punctuation(word, append_chars, white_space, prev_whitespace):
    PUNCTUATION_PLUS_SPACE = 2
    ctx = AppContext.get_current()
    at_start_of_buffer = len(ctx._buffer) <= PUNCTUATION_PLUS_SPACE
    space_length = len(white_space)
    if word in append_chars and space_length == 1 and not at_start_of_buffer:
        to_write = word + prev_whitespace
        backspace_count = len(prev_whitespace) + len(word) + 1
        backspace_then_write(backspace_count, to_write, update_expected=True)
        return True
    return False


def handle_new_space(
    left_part: str,
    right_part: str,
    white_space: str,
    new_flags: list[bool],
    config: Config,
) -> bool:
    if config.code.spacing_type != SpacingType.NEW:
        return False
    to_write, back_count = expand_new(
        left_part, new_flags, white_space, right_part, config
    )

    if back_count == 0 and to_write is None:
        return False

    backspace_then_write(back_count + 1, to_write)

    return True


def get_right_word() -> str:
    ctx = AppContext.get_current()
    if len(ctx._right_arrow_buffer.get_trailing_white_space()) == 0:
        return ctx._right_arrow_buffer.get_word(-1)[::-1]
    return ""


def get_left_right_part(word: str) -> tuple[str, str]:
    left_part = word
    right_part = get_right_word()
    return left_part, right_part


def handle_code_spacing(left_part, right_part, white_space, config: Config):

    if config.code.spacing_type != SpacingType.CODE:
        return False
    if len(white_space) > 1:
        left_part = ""

    if right_part == "" and is_valid_chip_str(left_part, config):
        return False

    casing = determine_code_casing(left_part, right_part)

    to_write, count = expand_code_casing(left_part, right_part, casing, config)

    if to_write is not None or count > 0:
        backspace_then_write(count + 1, to_write, update_expected=True)
        return True

    return False


def captlize_if_needed(to_write, to_write_is_str, config: Config):
    ctx = AppContext.get_current()
    capitalize_after = config.general.capitalize_after
    captlize_passthrough = config.rare.captlize_passthrough

    should_capitalize = (
        ctx.current_casing.is_normal_casing
        and ctx._buffer.should_captlize_prev_word(
            captilize_after=capitalize_after, pass_through=captlize_passthrough
        )
        and to_write_is_str
    )
    if should_capitalize:
        return captlize(to_write)
    return to_write


def escape_to_normal_casing(white_space):
    ctx = AppContext.get_current()
    if ctx.current_casing.is_not_normal_casing and white_space == "  ":
        activate_normal_casing_mode([])
        backspace(1)
        return True
    return False


def should_do_space_action(shift_down: bool, invert: bool) -> bool:
    return (shift_down and invert) or (not shift_down and not invert)


def handle_space(event: keyboard.KeyboardEvent, shift_down, config: Config):
    ctx = AppContext.get_current()
    append_chars = config.general.append_chars
    is_space = event.name == "space"
    pressed_key = event.event_type == keyboard.KEY_DOWN
    typing = ctx.expected_counter > 0

    if is_space and pressed_key and not typing:
        ctx._buffer.add(" ")
        white_space = ctx._buffer.get_trailing_white_space()
        if escape_to_normal_casing(white_space):
            return True

        if not should_do_space_action(shift_down, config.general.invert_space_actions):
            return True
        prev_whitespace = ctx._buffer.get_white_space_before_prev_word()
        word, flags = ctx._buffer.get_word_and_new_state(-1)
        prev_word = ctx._buffer.get_word(-2)

        if handle_space_punctuation(
            word, append_chars, white_space, prev_whitespace
        ):
            return True

        process_chip = len(white_space) == 1

        to_write: str | list[str] | None = None
        skip = False
        if process_chip:
            left_part, right_part = "", ""
            if ctx.current_casing == Casing.NORMAL:
                left_part, right_part = get_left_right_part(word)
                skip = is_all_non_alphanumeric_str(left_part)
                if not skip and handle_new_space(
                    left_part, right_part, white_space, flags, config
                ):
                    return True

                if not skip and handle_code_spacing(
                    left_part, right_part, white_space, config
                ):
                    return True

            to_write = get_chip_result(word, config)
            if not skip and to_write == word or to_write is None:
                to_write = expand_chunking(left_part, flags, config)

        if to_write is None:
            to_write = word

        to_write_is_str = is_str(to_write)
        to_write = captlize_if_needed(to_write, to_write_is_str, config)

        overlapping_start = 0
        prepended = 0

        if to_write_is_str:
            to_write, prepended, overlapping_start = convert_casing(
                to_write, word, prev_word, prev_whitespace, ctx.current_casing
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


def _process_event(event: keyboard.KeyboardEvent, config: Config):
    ctx = AppContext.get_current()
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

    if handle_if_release_event(event, config.general.toggle_case_on):
        return

    # ================EVERY EVENT BELOW THIS POINT IS GUARNEETD TO BE KEY DOWN=============

    if handle_space(event, shift_down, config):
        return

    name = event.name
    assert name is not None

    if name == "left":
        move_last(source=ctx._buffer, target=ctx._right_arrow_buffer)
        decrement_expected_counter()
        return
    elif name == "right":
        move_last(source=ctx._right_arrow_buffer, target=ctx._buffer)
        decrement_expected_counter()
        return
    elif name == "delete":
        ctx._right_arrow_buffer.remove_first()
        decrement_expected_counter()
        return

    utf: str | None = to_utf(name, shift_down)
    add_utf_and_update_expected(utf)


def process_event_wrapper(event: keyboard.KeyboardEvent):
    ctx = AppContext.get_current()
    should_update_new = (
        ctx.expected_counter == 0
        and event.name == "space"
        and event.event_type == keyboard.KEY_DOWN
    )
    _process_event(event, ctx.config)
    ctx.just_set.clear()
    if should_update_new:
        ctx._buffer.mark_recent_as_old()
        ctx._right_arrow_buffer.mark_recent_as_old()
    if ctx.expected_counter == 0:
        ctx.prev_real_event = event


def main():
    ctx = AppContext.initialize()

    keyboard.init(
        linux_collision_safety_mode=keyboard.LinuxCollisionSafetyModes.PATIENT
    )

    ipc_server = IPCServer(ctx.command_processor, ctx.config)
    ipc_server.start()

    def sigint_handler(*_):
        terminate([])

    original_handler = signal.signal(signal.SIGINT, sigint_handler)

    keyboard.hook(process_event_wrapper)
    try:
        ctx.stop_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        signal.signal(signal.SIGINT, original_handler)
        ipc_server.stop()


if __name__ == "__main__":
    main()
