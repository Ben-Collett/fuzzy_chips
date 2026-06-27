from config_utils import get_fuzzy_event_keyboard, get_fuzzy_event_button
from fuzzy_events import FuzzyEvent
from casing import Casing, convert_casing
from keyboard import mouse
from keyboard._mouse_event import ButtonEvent
from spacing_type import SpacingType
from collection_utils import captlize_word, count_where,  decrement_if_greater_than_zero, is_not_empty_str, decrement_if
from ipc_server import IPCServer
from utils import down_modifiers, safe_len, to_utf, is_str, is_only_shift_or_no_modifiers
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


def mouse_button_loop(event):
    if not isinstance(event, ButtonEvent):
        return
    events = get_fuzzy_event_button(
        event, AppContext.get_current().config)

    regular_clear = FuzzyEvent.clear_buffer.value in events
    safe_clear = FuzzyEvent.clear_buffer_ipc_safe.value in events
    if handle_clear(regular_clear, safe_clear):
        return

    delete_prev = FuzzyEvent.delete_word.value in events
    if delete_prev:
        delete_previous_word()
        return

    if FuzzyEvent.toggle_case.value in events:
        toggle_prev_word_casing()
        return


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
    set_buffer(args[::-1], AppContext.get_current().right_arrow_buffer)


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
    ctx.expected_counter = decrement_if_greater_than_zero(ctx.expected_counter)


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


def delete_previous_word(backspace_offset: int = 0):
    ctx = AppContext.get_current()
    buffer = ctx._buffer.get()

    back_count = max(
        determine_amount_to_backspace_shift_backspace(buffer)-backspace_offset, 0)
    to_write = ""
    if (
        ctx.current_casing.is_not_normal_casing
        and len(buffer) - back_count - len(ctx._buffer.get_leading_white_space()) > 1
    ):
        to_write = " "

    while backspace_offset > 0:
        ctx._buffer.backspace()
        backspace_offset -= 1

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
            # +1 to delete the punctuation mark
            backspace_count = len(leading_whitespace) + 1
            to_write = name + leading_whitespace
            backspace_then_write(backspace_count, to_write,
                                 update_expected=True)

            return True
    return False


def toggle_prev_word_casing():
    ctx = AppContext.get_current()
    word = ctx._buffer.get_last_word()
    white_space = ctx._buffer.get_trailing_white_space()

    back_count, to_write = shift_press_release(word, white_space)
    backspace_then_write(back_count, to_write, update_expected=True)


def handle_clear(regular_clear: bool, safe_clear: bool):
    should_clear = regular_clear
    ctx = AppContext.get_current()
    if not ctx.just_set.is_set() and safe_clear:
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


def handle_expand_punctuation(word, append_chars, white_space, prev_whitespace):
    """
    word = the punctuation mark
    append_chars the list of characters that should
    be appended as punctatoin
    white_space = space after the punctuation mark
    prev_whitespace = space before the punctuation mark
    """
    PUNCTUATION_PLUS_SPACE = 2
    ctx = AppContext.get_current()
    at_start_of_buffer = len(ctx._buffer) <= PUNCTUATION_PLUS_SPACE
    prev_space_length = len(prev_whitespace)

    if word in append_chars and prev_space_length > 0 and not at_start_of_buffer:
        to_write = word + prev_whitespace
        backspace_count = prev_space_length + len(word) + len(white_space)
        backspace_then_write(backspace_count, to_write, update_expected=True)
        return True
    return False


def handle_new_space(
    left_part: str,
    right_part: str,
    white_space: str,
    new_flags: list[bool],
    trigger_utf: str | None,
    config: Config,
) -> bool:
    if config.code.spacing_type != SpacingType.NEW:
        return False
    to_write, back_count = expand_new(
        left_part, new_flags, white_space, right_part, config
    )

    if back_count == 0 and to_write is None:
        return False

    backspace_then_write(back_count + safe_len(trigger_utf), to_write)

    return True


def get_right_word() -> str:
    ctx = AppContext.get_current()
    if len(ctx.right_arrow_buffer.get_leading_white_space()) == 0:
        return ctx.right_arrow_buffer.get_word(-1)[::-1]
    return ""


def handle_code_spacing(left_part: str, right_part: str, white_space: str, config: Config) -> bool:

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
    """
    something to consider right now hi. 12+abc would captlzie the A is that what a I want? Does it matter?
    """
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
        return captlize_word(to_write)
    return to_write


def escape_to_normal_casing(white_space: str, event_utf: str | None):
    event_utf = event_utf or ""
    ctx = AppContext.get_current()
    white_space_length = len(white_space)
    white_space_length = decrement_if(white_space_length, event_utf.isspace())

    if ctx.current_casing.is_not_normal_casing and white_space_length > 0:
        activate_normal_casing_mode([])
        if len(event_utf) == 1:
            backspace(1)
        return True
    return False


def handle_expand(config: Config, event_name_utf=""):
    ctx = AppContext.get_current()
    buffer = ctx._buffer
    append_chars = config.general.append_chars

    white_space = ctx._buffer.get_trailing_white_space()

    # TODO: figure out how to handle this
    if escape_to_normal_casing(white_space, event_name_utf):
        return True

    prev_whitespace = buffer.get_white_space_before_prev_word()
    word, flags = buffer.get_word_and_new_state(-1)
    prev_word = buffer.get_word(-2)

    if handle_expand_punctuation(
        word, append_chars, white_space, prev_whitespace
    ):
        return True

    process_chip = len(white_space) <= 1

    to_write: str | list[str] | None = None
    skip = False
    if process_chip:
        left_part, right_part = "", ""
        if ctx.current_casing == Casing.NORMAL:
            left_part = word
            right_part = get_right_word()
            skip = is_all_non_alphanumeric_str(
                left_part) or get_chip_result(left_part, config) is not None
            if not skip and handle_new_space(
                left_part, right_part, white_space, flags, event_name_utf, config
            ):
                return True

            if not skip and handle_code_spacing(
                left_part, right_part, white_space, config
            ):
                return True

        to_write = get_chip_result(word, config)
        if left_part != "" and (not skip and to_write == word or to_write is None):
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
        to_backspace_count = len(
            word) + safe_len(event_name_utf) - overlapping_start + prepended
        if to_write_is_str:
            utf = event_name_utf or ""
            if utf.isspace():
                to_write += utf
            else:
                to_write += " "
        backspace_then_write(to_backspace_count,
                             to_write, update_expected=True)


def _process_event(event: keyboard.KeyboardEvent, config: Config):
    ctx = AppContext.get_current()

    down_mods = down_modifiers(event)
    if ctx.expected_counter == 0:
        events = get_fuzzy_event_keyboard(
            event, ctx.prev_real_event, down_mods, config)
    else:
        events = []

    regular_clear = FuzzyEvent.clear_buffer.value in events
    safe_clear = FuzzyEvent.clear_buffer_ipc_safe.value in events
    if handle_clear(regular_clear, safe_clear):
        return

    if handle_auto_append(event, config):
        return

    utf: str | None = None
    is_pressed = event.event_type == keyboard.KEY_DOWN
    if is_pressed:
        name = event.name
        assert name is not None

        if name == "left":
            move_last(source=ctx._buffer, target=ctx.right_arrow_buffer)
            decrement_expected_counter()
        elif name == "right":
            move_last(source=ctx.right_arrow_buffer, target=ctx._buffer)
            decrement_expected_counter()
        elif name == "delete":
            ctx.right_arrow_buffer.remove_first()
            decrement_expected_counter()
        else:
            utf = to_utf(name)
            is_displayed_key = utf and (utf.isprintable() or utf.isspace())
            if is_displayed_key and is_only_shift_or_no_modifiers(event):
                ctx._buffer.add(utf)
                decrement_expected_counter()

    delete_prev = FuzzyEvent.delete_word.value in events
    if delete_prev:
        if event.name == "backspace" and is_pressed:
            delete_previous_word(backspace_offset=1)
        else:
            delete_previous_word()
        return

    if is_pressed and event.name == "backspace":
        ctx._buffer.backspace()
        decrement_expected_counter()

    # ============post buffer update========================
    if FuzzyEvent.toggle_case.value in events:
        toggle_prev_word_casing()
        return

    should_expand = FuzzyEvent.expand.value in events
    if should_expand:
        handle_expand(config, utf or "")


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
        ctx.right_arrow_buffer.mark_recent_as_old()
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
    mouse.hook(mouse_button_loop)
    try:
        ctx.stop_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        signal.signal(signal.SIGINT, original_handler)
        ipc_server.stop()


if __name__ == "__main__":
    main()
