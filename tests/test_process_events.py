from config import Config
from keyboard import KeyboardEvent
from main import process_event_wrapper, mouse_button_loop
from mocks import AppContextMock, ConfigWrapperMock, KeyboardMock
from casing import Casing
from main_context import AppContext
from testing_utils import events_from_text
import pytest


SIMPLE_CHIPS = {"t": "the", "th": "that", "h": "here", "e": "then", "tg": "thing", "rl": [
    "reload_config"], "ger": ["g", "r", "e", "e", "backspace", "a", "t"],
    # change case
    "-": ["kebab-case-mode"],
    "nm": ["normal case mode"],
    "_": ["snake_case_mode"],
    "__": ["UPPER_SNAKE_CASE_MODE"],
    "pm": ["ProperCaseMode"],
    "cmm": ["camelCaseMode"],
}


def buff_equals(ctx: AppContext, expected: str) -> bool:
    return "".join(ctx._buffer.get()) == expected


def assert_buff_equals(ctx: AppContext, expected: str) -> None:
    assert "".join(ctx._buffer.get()) == expected


def assert_buffers_empty(ctx: AppContext):
    assert ctx._buffer.get() == []
    assert ctx.right_arrow_buffer.get() == []


def _make_simple_override(overrides: dict):
    """
    changes overrides in place and returns it
    """
    if "chips" not in overrides:
        overrides["chips"] = SIMPLE_CHIPS
    return overrides


def _make_basic_config_wrapper(config_override=None) -> ConfigWrapperMock:
    chips_only = _make_simple_override({})
    if config_override is None:
        config_override = chips_only
    mock = ConfigWrapperMock(Config(config_override))
    mock.set_on_reload(chips_only)
    return mock


def _process_events(events: list[KeyboardEvent], config_override: dict | None = None, ctx: AppContextMock | None = None) -> AppContextMock:
    if ctx is None:
        config = _make_basic_config_wrapper(config_override)
        ctx = AppContextMock(config)
    AppContext.initialize(ctx)
    keyboard = ctx.keyboard
    assert isinstance(keyboard, KeyboardMock), "keyboard not a mock"

    if len(keyboard.callbacks) == 0:
        keyboard.hook(process_event_wrapper)
    keyboard.events_to_run.extend(events)
    keyboard.flush_events_to_run()

    return ctx


def _make_contextlr(left: str, right: str, config_override=None, recent=True):
    config = _make_basic_config_wrapper(config_override)
    ctx = AppContextMock(config)
    ctx._buffer.set_buffer([*left], recent)
    ctx.right_arrow_buffer.set_buffer([*right], recent)
    AppContext.initialize(ctx)
    return ctx


class WritingTest:
    @pytest.mark.parametrize(
        ("text", "left", "right"),
        [
            ("hit<left><left><delete>", "h", "t")

        ],
    )
    def test_expand_space(self, text: str, left, right):
        ctx = _process_events(events_from_text(text))
        assert "".join(ctx._buffer.get()) == left
        assert "".join(ctx.right_arrow_buffer.get()) == right

# doesn't test changing casing just expanding to text
# that's covered by another class


class TestTextExpand:
    @pytest.mark.parametrize(
        ("text", "expected_buffer_state"),
        [
            ("t ", "the "),
            ("T ", "The "),
            ("TH ", "THAT "),
            ("t. th ", "the. That "),
            ('"t." ', '"the." '),
            (" hi there ", " hi there "),
            ("th ", "that "),
            ("ht ", "that "),
            ("t th ", "the that "),
            ("t th ", "the that "),
            ("t<shift:down> ", "t "),

        ],
    )
    def test_expand_space(self, text: str, expected_buffer_state: str):
        ctx = _process_events(events_from_text(text))
        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(
        ("text", "expected_buffer_state"),
        [
            ("t<menu>", "the "),
            ("tH<menu>", "That "),
            ("TH<menu>", "THAT "),
            (" hi there<menu>", " hi there"),
            ("th.<menu>", "that. "),
            ("ht<menu>", "that "),
            ("t<menu>th<menu>", "the that "),
            ("t<shift:down><menu>", "t"),

        ],
    )
    def test_expand_menu(self, text: str, expected_buffer_state: str):
        override = _make_simple_override({"on_press": {"menu": "expand"}})
        ctx = _process_events(events_from_text(text), config_override=override)
        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(
        ("text", "expected_buffer_state"),
        [
            ("t\n", "the\n"),
            (" hi there\n", " hi there\n"),
            ("th\n", "that\n"),
            ("ht\n", "that\n"),
            ("t\nth\n", "the\nthat\n"),
            ("t<shift:down>\n", "t\n"),

        ],
    )
    def test_expand_enter(self, text: str, expected_buffer_state: str):
        override = _make_simple_override({"on_press": {"enter": "expand"}})
        ctx = _process_events(events_from_text(text), config_override=override)
        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(
        ("text", "expected_buffer_state"),
        [
            ("th t ", "th t "),
            ("th<shift:down> <shift:up>t<shift:down> ", "that the "),
            ("th t<shift:down> ", "th the "),

        ],
    )
    def test_shift_space(self, text: str, expected_buffer_state: str):
        override = _make_simple_override(
            {"on_press": {"shift+space": "expand"}})
        ctx = _process_events(events_from_text(text), config_override=override)
        assert_buff_equals(ctx, expected_buffer_state)

    # it works, but I truly hope no one ever does this
    @pytest.mark.parametrize(
        ("text", "expected_buffer_state"),
        [
            ("th t ", "th t "),
            ("th<shift:down><shift:up>t<shift:down><shift:up>", "that the "),
            ("th t<shift:down><shift:up>", "th the "),

        ],
    )
    def test_toggle_expand(self, text: str, expected_buffer_state: str):
        override = _make_simple_override(
            {"on_press": {}, "on_toggle": {"shift": "expand"}})
        ctx = _process_events(events_from_text(text), config_override=override)
        assert_buff_equals(ctx, expected_buffer_state)

    def test_list_expand(self):
        text = "ger "
        expected = ["backspace", "backspace", "backspace",
                    "backspace", "g", "r", "e", "e", "backspace", "a", "t"]
        ctx = _process_events(events_from_text(text))
        assert ctx.written_event_names() == expected


DELETE_WORD_CASES = [
    ("the", "", "", 3),
    ("the long", "", "the ", 4),
    ("the Long", "what ever", "the ", 4),
    ("theLong", "what ever", "the", 4),
    ("TheLong", "what ever", "The", 4),
    ("the-Long", "what ever", "the-", 4),
    ("The_Long", "what ever", "The_", 4),
    ("The_", "what ever", "", 4),
    ("the ", "what ever", "", 4),
    ("the_cool_thing_", "", "the_cool_", 6),
]


class TestDeleteWord:
    @pytest.mark.parametrize(("left_state", "right_state", "expected_buffer_state", "expected_backspace_count"),
                             DELETE_WORD_CASES)
    def test_delete_word_shift_backspace(self, left_state: str,  right_state: str, expected_buffer_state: str, expected_backspace_count: int):
        ctx = _make_contextlr(left_state, right_state)
        _process_events(events_from_text("<shift:down><bs>"), ctx=ctx)
        assert list(right_state) == ctx.right_arrow_buffer.get(
        ), f"deleting a word shouldn't change the state of the right buffer {list(right_state)} != {ctx.right_arrow_buffer.get()}"

        assert_buff_equals(ctx, expected_buffer_state)
        assert ctx.count_writes("backspace") == expected_backspace_count-1

    @pytest.mark.parametrize(("left_state", "right_state", "expected_buffer_state", "expected_backspace_count"), DELETE_WORD_CASES)
    def test_delete_word_menu(self, left_state: str,  right_state: str, expected_buffer_state: str, expected_backspace_count: int):
        override = _make_simple_override({"on_press": {"menu": "delete_word"}})
        ctx = _make_contextlr(left_state, right_state,
                              config_override=override)
        _process_events(events_from_text("<menu>"), ctx=ctx)
        assert ctx.count_writes("backspace") == expected_backspace_count

        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("left_state", "right_state", "expected_buffer_state", "expected_backspace_count"), DELETE_WORD_CASES)
    def test_delete_on_toggle(self, left_state: str, right_state: str,  expected_buffer_state: str, expected_backspace_count: int):
        override = _make_simple_override(
            {"on_toggle": {"shift": "delete_word"}})
        ctx = _make_contextlr(left_state, right_state,
                              config_override=override)
        _process_events(events_from_text("<shift:down><shift:up>"), ctx=ctx)
        assert ctx.count_writes("backspace") == expected_backspace_count

        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("left_state", "right_state", "expected_buffer_state", "expected_backspace_count"),
                             DELETE_WORD_CASES
                             )
    def test_delete_on_left_click(self, left_state: str, right_state: str,   expected_buffer_state: str, expected_backspace_count: int):
        override = _make_simple_override(
            {"on_mouse_button_down": {"left": "delete_word"}})
        ctx = _make_contextlr(left_state, right_state, override)
        ctx.mouse.hook(mouse_button_loop)
        # TODO: I should come up with a way to write this kind of test that
        # doesn't require manually hooking and flushing the keyboard buffer
        ctx.keyboard.hook(process_event_wrapper)
        ctx.left_click()

        assert isinstance(ctx.keyboard, KeyboardMock), "keyboard not a mock"
        ctx.keyboard.flush_events_to_run()

        assert ctx.count_writes("backspace") == expected_backspace_count

        assert_buff_equals(ctx, expected_buffer_state)


class TestClearBuffer:
    @pytest.mark.parametrize(("left_state", "right_state"), [("hi", ""), ("", "hi"), (" h32i", " t234here ")])
    def test_clear_on_meta(self, left_state, right_state):
        ctx = _make_contextlr(left_state, right_state)
        _process_events(events_from_text("<windows:down>"), ctx=ctx)

        assert_buffers_empty(ctx)

    @pytest.mark.parametrize(("left_state", "right_state"), [("hi", ""), ("", "hi"), (" h32i", " t234here ")])
    def test_clear_on_menu(self, left_state, right_state):
        override = _make_simple_override(
            {"on_press": {"menu": "clear_buffer"}})
        ctx = _make_contextlr(left_state, right_state, override)
        _process_events(events_from_text("<menu:down>"), ctx=ctx)

        assert_buffers_empty(ctx)

    @pytest.mark.parametrize(("left_state", "right_state"), [("hi", ""), ("", "hi"), (" h32i", " t234here ")])
    def test_clear_on_toggle_shift(self, left_state, right_state):
        override = _make_simple_override(
            {"on_toggle": {"shift": "clear_buffer"}})
        ctx = _make_contextlr(left_state, right_state, override)
        _process_events(events_from_text("<shift:down><shift:up>"), ctx=ctx)

        assert_buffers_empty(ctx)

    @pytest.mark.parametrize(("left_state", "right_state"), [("hi", ""), ("", "hi"), (" h32i", " t234here ")])
    def test_clear_left_click(self, left_state, right_state):
        ctx = _make_contextlr(left_state, right_state)
        ctx.mouse.hook(mouse_button_loop)
        ctx.left_click()

        assert_buffers_empty(ctx)


class TestActivateCaseModes:
    def test_activate_snake(self):
        ctx = _process_events(events_from_text("_ "))
        assert ctx.current_casing == Casing.SNAKE

    def test_activate_upper_snake(self):
        ctx = _process_events(events_from_text("__ "))
        assert ctx.current_casing == Casing.UPPER_SNAKE

    def test_activate_upper_kebab(self):
        ctx = _process_events(events_from_text("- "))
        assert ctx.current_casing == Casing.KEBAB

    def test_activate_cammel(self):
        ctx = _process_events(events_from_text("cmm "))
        assert ctx.current_casing == Casing.CAMEL

    def test_activate_proper(self):
        ctx = _process_events(events_from_text("pm "))
        assert ctx.current_casing == Casing.PROPER


class TestTypingCaseMode:
    @pytest.mark.parametrize(("initial_state", "text", "expected_buffer_state"), [
        ("hi", "", "hi "),
        ("person", "thing", "personthing "),
        ("person ", "thing", "person_thing "),
        ("what's ", "th", "what's_that "),
        ("what's ", "th t", "what's_that_the "),
        ("the_thing ", "is_that", "the_thing_is_that "),
        ("the_thing ", "_", "the_thing "),
        ("the_thing- ", "that", "the_thing- that "),
        ("the_thing. ", "that", "the_thing.that "),
    ])
    def test_snake(self, initial_state: str, text: str, expected_buffer_state: str):
        text += " "

        ctx = _make_contextlr(initial_state, "")
        ctx.current_casing = Casing.SNAKE
        _process_events(events_from_text(text), ctx=ctx)
        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("initial_state", "text", "expected_buffer_state"), [
        ("hi", "", "hi "),
        ("person", "thing", "personthing "),
        ("person ", "thing", "person thing "),
        ("what's ", "th", "what's that "),
        ("what's ", "th t", "what's that the "),
        ("the_thing ", "is_that", "the_thing is_that "),
        ("the_thing ", "_", "the_thing "),
        ("the_thing- ", "that", "the_thing- that "),
        ("the_thing. ", "that", "the_thing. That "),
    ])
    def test_normal(self, initial_state: str, text: str, expected_buffer_state: str):
        text += " "

        ctx = _make_contextlr(initial_state, "")
        ctx.current_casing = Casing.NORMAL
        _process_events(events_from_text(text), ctx=ctx)

        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("initial_state", "text", "expected_buffer_state"), [
        ("hi", "", "hi "),
        ("person", "thing", "personthing "),
        ("person ", "thing", "person-thing "),
        ("what's ", "th", "what's-that "),
        ("what's ", "th t", "what's-that-the "),
        ("the-thing ", "is_that", "the-thing-is_that "),
        ("the-thing ", "-", "the-thing "),
        ("the-thing- ", "that", "the-thing-that "),
        ("the-thing. ", "that", "the-thing. That "),
    ])
    def test_kebab(self, initial_state: str, text: str, expected_buffer_state: str):
        text += " "

        ctx = _make_contextlr(initial_state, "")
        ctx.current_casing = Casing.KEBAB
        _process_events(events_from_text(text), ctx=ctx)

        assert_buff_equals(ctx, expected_buffer_state)

    # TODO:
    # I wonder if there is a nicer way to handle this
    # it's probably not great to append UPPER_SNAKE case
    # test to lower text
    @pytest.mark.parametrize(("initial_state", "text", "expected_buffer_state"), [
        ("hi", "", "HI "),
        ("person", "thing", "PERSONTHING "),
        ("person ", "thing", "person_THING "),
        ("what's ", "th", "what's_THAT "),
        ("what's ", "th t", "what's_THAT_THE "),
        ("the_thing ", "is_that", "the_thing_IS_THAT "),
        ("the_thing ", "_", "the_thing "),
        ("the_thing- ", "that", "the_thing- THAT "),
        ("the_thing. ", "that", "the_thing.THAT "),
    ])
    def test_upper_snake(self, initial_state: str, text: str, expected_buffer_state: str):
        text += " "

        ctx = _make_contextlr(initial_state, "")
        ctx.current_casing = Casing.UPPER_SNAKE
        _process_events(events_from_text(text), ctx=ctx)

        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("initial_state", "text", "expected_buffer_state"), [
        ("hi", "", "hi "),
        ("person", "thing", "personthing "),
        ("person ", "thing", "personThing "),
        ("what's ", "th", "what'sThat "),
        ("what's ", "th t", "what'sThatThe "),
        ("theThing ", "isThat", "theThingIsThat "),
        ("theThing ", "cmm", "theThing "),
        ("theThing- ", "that", "theThing- that "),
        ("theThing. ", "that", "theThing.that "),
    ])
    def test_camel(self, initial_state: str, text: str, expected_buffer_state: str):
        text += " "

        ctx = _make_contextlr(initial_state, "")
        ctx.current_casing = Casing.CAMEL
        _process_events(events_from_text(text), ctx=ctx)

        assert_buff_equals(ctx, expected_buffer_state)

    # TODO: again same problem as upper snake casse with the personThing test
    @pytest.mark.parametrize(("initial_state", "text", "expected_buffer_state"), [
        ("hi", "", "Hi "),
        ("person", "thing", "Personthing "),
        ("person ", "thing", "personThing "),
        ("what's ", "th", "what'sThat "),
        ("what's ", "th t", "what'sThatThe "),
        ("TheThing ", "IsThat", "TheThingIsThat "),
        ("theThing ", "pm", "theThing "),
        ("theThing- ", "that", "theThing- That "),
        ("TheThing. ", "that", "TheThing.That "),
    ])
    def test_proper(self, initial_state: str, text: str, expected_buffer_state: str):
        text += " "

        ctx = _make_contextlr(initial_state, "")
        ctx.current_casing = Casing.PROPER
        _process_events(events_from_text(text), ctx=ctx)

        assert_buff_equals(ctx, expected_buffer_state)


class TestReloadConfig:
    def test_reload(self):
        ctx = _make_contextlr("", "")
        rl_events = events_from_text("rl ")
        for i in range(10):
            assert ctx.reload_count() == i
            ctx = _process_events(rl_events, ctx=ctx)
        assert ctx.reload_count() == 10


CAPTLIZATION_CASES = [
    ("", ""),
    ("h", "H"),
    ("hello", "Hello"),
    ("hello ", "Hello "),
    ("hello_ ", "HELLO_ "),
    ("_hello ", "_Hello "),
    ("--23hello23-- ", "--23Hello23-- "),
    ("'\"hello'\"", "'\"Hello'\""),
    ("hello-there ", "hello-There "),
    ("hello_there", "HELLO_THERE"),
    ("HELLO_THERE", "hello_there"),
    ("HEllo_there", "hello_there"),
    ("hello_thEre", "hello_there")
]


class TestToggleCase:
    @pytest.mark.parametrize(("initial_state", "expected_buffer_state"), CAPTLIZATION_CASES)
    def test_toggle_on_shift(self, initial_state, expected_buffer_state):
        ctx = _make_contextlr(initial_state, "")
        _process_events(events_from_text("<shift>"), ctx=ctx)

        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("initial_state", "expected_buffer_state"), CAPTLIZATION_CASES)
    def test_toggle_on_menu(self, initial_state, expected_buffer_state):
        override = _make_simple_override({"on_press": {"menu": "toggle_case"}})
        ctx = _make_contextlr(initial_state, "", override)
        _process_events(events_from_text("<menu>"), ctx=ctx)
        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("initial_state", "expected_buffer_state"), CAPTLIZATION_CASES)
    def test_toggle_on_left_click(self, initial_state, expected_buffer_state):
        override = _make_simple_override(
            {"on_mouse_button_down": {"left": "toggle_case"}})
        ctx = _make_contextlr(initial_state, "", override)
        ctx.mouse.hook(mouse_button_loop)
        # TODO: I should come up with a way to write this kind of test that
        # doesn't require manually hooking and flushing the keyboard buffer
        ctx.keyboard.hook(process_event_wrapper)
        ctx.left_click()

        assert isinstance(ctx.keyboard, KeyboardMock), "keyboard not a mock"
        ctx.keyboard.flush_events_to_run()

        assert_buff_equals(ctx, expected_buffer_state)


class TestAppendPunctuation:
    @pytest.mark.parametrize(("text", "expected_buffer_state"), [
        (",", ","),
        ("hi ,", "hi, "),
        ("this is hi .?,", "this is hi.?, "),
        ("this  \n!", "this!  \n"),
    ])
    def test_auto_append(self, text, expected_buffer_state):
        override = _make_simple_override({"general": {"auto_append": True}})
        events = events_from_text(text)
        ctx = _process_events(events, override)
        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("text", "expected_buffer_state"), [
        (",", ","),
        ("hi ,", "hi ,"),
        ("hi , ", "hi, "),
        ("hi ,<shift:down> ", "hi , "),
        ("this is hi .? ", "this is hi .? "),
        ("this  \n! ", "this!  \n"),
    ])
    def test_manual_append(self, text, expected_buffer_state):
        events = events_from_text(text)
        ctx = _process_events(events)
        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("text", "expected_buffer_state"), [
        (",", ","),
        ("hi , ", "hi , "),
        ("hi ,<menu>", "hi, "),
        ("this is hi .?<menu>", "this is hi .?"),
        ("this  \n!<menu>", "this!  \n"),
    ])
    def test_manual_append_menu(self, text, expected_buffer_state):
        override = _make_simple_override({"on_press": {"menu": "expand"}})
        events = events_from_text(text)
        ctx = _process_events(events, override)
        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("text", "expected_buffer_state"), [
        ("t", "t"),
        ("the . ", "the . "),
        ("hi t", "hit "),
        ("this . t", "this .t ")
    ])
    def test_auto_append_override(self, text, expected_buffer_state):
        override = _make_simple_override({"general": {
            "auto_append": True, "append_chars": ["t"]}})
        events = events_from_text(text)
        ctx = _process_events(events, override)
        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("text", "expected_buffer_state"), [
        ("g", "g"),
        ("hi g", "hi g"),
        ("hi g ", "hig "),
        ("this . g ", "this .g ")
    ])
    def test_manual_override(self, text, expected_buffer_state):
        override = _make_simple_override({"general": {"append_chars": ["g"]}})
        events = events_from_text(text)
        ctx = _process_events(events, override)
        assert_buff_equals(ctx, expected_buffer_state)


class TestAutoCaptlize:

    @pytest.mark.parametrize(("text", "expected_buffer_state"), [
        ("the. thing ", "the. Thing "),
        (".the thing ", ".the thing "),
        ('"the.""" thing ', '"the.""" Thing '),
        ("the... thing ", "the... Thing "),
        ("the. th ", "the. That "),
    ])
    def test_auto_captlize(self, text, expected_buffer_state):
        events = events_from_text(text)
        ctx = _process_events(events)
        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("text", "expected_buffer_state"), [
        ("the. thing ", "the. thing "),
        ('"lt""" thing ', '"lt""" Thing '),
        ("het th ", "het That "),
    ])
    def test_override_captlize_after(self, text, expected_buffer_state):
        override = _make_simple_override({"general":
                                          {"capitalize_after": ["t"]}})
        events = events_from_text(text)
        ctx = _process_events(events, override)

        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("text", "expected_buffer_state"), [
        (".g thing ", ".g Thing "),
        ("g. thing ", "g. Thing "),
        ("g thing ", "g thing "),
        ("g.' thing ", "g.' thing "),
    ])
    def test_override_passthrough(self, text, expected_buffer_state):
        override = _make_simple_override({"rare":
                                          {"capitalize_passthrough": ["g"]}})
        events = events_from_text(text)
        ctx = _process_events(events, override)

        assert_buff_equals(ctx, expected_buffer_state)


class TestExpandWithSmallBuffer:
    @pytest.mark.parametrize(("text", "expected_buffer_state", "size"), [
        ("tl ", "l ", 2),
        ("th ", "e ", 2),  # Expands "h " to here
        ("th ", "at ", 3),  # Expands "h " to here
        ("t ", "e ", 2),
        ("t th t ", "he ", 3)
    ])
    def test_expand_with_small_buffer(self, text, expected_buffer_state, size):
        override = _make_simple_override({"general":
                                          {"buffer_size": size}})
        events = events_from_text(text)
        ctx = _process_events(events, override)

        assert_buff_equals(ctx, expected_buffer_state)


class TestChunking:
    @pytest.mark.parametrize(("text", "expected_buffer_state"), [
        ("th-tg ", "th-thing "),
        ("th+tg ", "th+thing "),
        ("th_tg ", "th_tg "),
        ("th'tg ", "th'tg ")
    ])
    def test_expand_last(self, text, expected_buffer_state):
        events = events_from_text(text)
        ctx = _process_events(events)
        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("text", "expected_buffer_state"), [
        ("th-tg ", "th-tg "),
        ("th+tg ", "th+tg "),
        ("th'tg ", "th'tg ")
    ])
    def test_expand_none(self, text, expected_buffer_state):

        override = _make_simple_override(
            {"chunking": {"chunking_type": "none"}})
        events = events_from_text(text)
        ctx = _process_events(events, override)
        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("text", "expected_buffer_state"), [
        ("th-tg ", "that-thing "),
        ("th+tg ", "that+thing "),
        ("th'tg ", "th'tg ")
    ])
    def test_expand_all(self, text, expected_buffer_state):
        override = _make_simple_override(
            {"chunking": {"chunking_type": "all"}})
        events = events_from_text(text)
        ctx = _process_events(events, override)
        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("text", "expected_buffer_state"), [
        ("th-tg ", "th-tg "),
        ("th+tg ", "th+tg "),
        ("th'tg ", "th'thing ")
    ])
    def test_expand_ignore(self, text, expected_buffer_state):
        override = _make_simple_override(
            {"chunking": {"chunking_ignore": ["+", "-"]}})
        events = events_from_text(text)
        ctx = _process_events(events, override)
        assert_buff_equals(ctx, expected_buffer_state)

    @pytest.mark.parametrize(("initial_state", "new_str", "expected_buffer_state"), [
        ("th-tg", "00000", "th-tg "),
        ("th-tg", "00011", "th-thing "),
        ("th-tg", "11111", "that-thing "),
        ("tg-th", "00001", "tg-th "),
        ("th", "01", "that "),  # chunking should have no effect
    ])
    def test_expand_new(self, initial_state, new_str, expected_buffer_state):
        assert len(initial_state) == len(new_str)
        override = _make_simple_override(
            {"chunking": {"chunking_type": "new", "new_chunks_only": True}})

        ctx = _make_contextlr("", "", override)
        for ch, flag in zip(initial_state, new_str):
            if flag == "1":
                ctx._buffer.add(ch)
            else:
                ctx._buffer.add(ch, recent=False)

        events = events_from_text(" ")
        _process_events(events, ctx=ctx)

        assert_buff_equals(ctx, expected_buffer_state)


class TestNewCasing:
    @pytest.mark.parametrize(("left", "right", "text", "expected"), [
        ("theThingGood", "Long", "t ", "theThingGoodTheLong"),
        ("theCoolPerson", "could", "wow ", "theCoolPersonWowCould"),
        ("theCoolPerson", "could", "Wow ", "theCoolPersonWowCould"),
        ("theCoolPerson", "Could", "wow ", "theCoolPersonWowCould"),
        ("theCoolPerson", "", "t ", "theCoolPersonThe"),
        ("theCoolPerson", "", "the ", "theCoolPersonThe"),
        # ("", "CoolPerson", "t ", "TheCoolPerson"), # maybe I should expand at beginning?
    ])
    def test_new_cammel(self, left, right, text, expected):
        ctx = _make_contextlr(
            left, right[::-1], _make_simple_override({"code": {"spacing_type": "new"}}), recent=False)
        events = events_from_text(text)
        _process_events(events, ctx=ctx)
        actual = ctx.buffers_to_str()
        assert actual == expected

    @pytest.mark.parametrize(("left", "right", "text", "expected"), [
        ("the_thing_good", "long", "t ", "the_thing_good_the_long"),
        ("the_thing_good", "_long", "t ", "the_thing_good_the_long"),
        ("the_thing_good_", "_long", "t ", "the_thing_good_the_long"),
        ("the_thing_good_", "long", "t ", "the_thing_good_the_long"),
        ("the_cool_person", "_could", "wow ", "the_cool_person_wow_could"),
        ("the_cool_person", "could", "wow ", "the_cool_person_wow_could"),
        ("the_cool_person_", "could", "wow ", "the_cool_person_wow_could"),
        ("the_cool_person", "", "t ", "the_cool_person_the"),
        ("the_cool_person", "", "the ", "the_cool_person_the"),
        # ("", "cool_person", "t ", "the_cool_person"), # maybe I should expand at beginning?
    ])
    def test_new_snake(self, left, right, text, expected):
        ctx = _make_contextlr(
            left, right[::-1], _make_simple_override({"code": {"spacing_type": "new"}}), recent=False)
        events = events_from_text(text)
        _process_events(events, ctx=ctx)
        actual = ctx.buffers_to_str()
        assert actual == expected

    @pytest.mark.parametrize(("left", "right", "text", "expected"), [
        ("THE_THING_GOOD", "LONG", "t ", "THE_THING_GOOD_THE_LONG"),
        ("THE_THING_GOOD", "_LONG", "t ", "THE_THING_GOOD_THE_LONG"),
        ("THE_THING_GooD", "_LONG", "t ", "THE_THING_GooD_THE_LONG"),
        ("THE_THING_GOOD", "LONG", "t ", "THE_THING_GOOD_THE_LONG"),
        ("THE_COOL_PERSON", "_COULD", "wow ", "THE_COOL_PERSON_WOW_COULD"),
        ("THE_COOL_PERSON", "COULD", "wow ", "THE_COOL_PERSON_WOW_COULD"),
        ("THE_COOL_PERSON", "COULD", "wow ", "THE_COOL_PERSON_WOW_COULD"),
        ("THE_COOL_PERSON", "", "t ", "THE_COOL_PERSON_THE"),
        ("THE_COOL_PERSON", "", "the ", "THE_COOL_PERSON_THE"),
    ])
    def test_upper_snake(self, left, right, text, expected):
        ctx = _make_contextlr(
            left, right[::-1], _make_simple_override({"code": {"spacing_type": "new"}}), recent=False)
        events = events_from_text(text)
        _process_events(events, ctx=ctx)
        actual = ctx.buffers_to_str()
        assert actual == expected

    @pytest.mark.parametrize(("left", "right", "text", "expected"), [
        ("TheThingGood", "Long", "t ", "TheThingGoodTheLong"),
        ("TheCoolPerson", "could", "wow ", "TheCoolPersonWowCould"),
        ("TheCoolPerson", "could", "Wow ", "TheCoolPersonWowCould"),
        ("TheCoolPerson", "Could", "wow ", "TheCoolPersonWowCould"),
        ("TheCoolPerson", "", "t ", "TheCoolPersonThe"),
        ("TheCoolPerson", "", "the ", "TheCoolPersonThe"),
        # ("", "CoolPerson", "t ", "TheCoolPerson"), # maybe I should expand at beginning?
    ])
    def test_proper_case(self, left, right, text, expected):
        ctx = _make_contextlr(
            left, right[::-1], _make_simple_override({"code": {"spacing_type": "new"}}), recent=False)
        events = events_from_text(text)
        _process_events(events, ctx=ctx)
        actual = ctx.buffers_to_str()
        assert actual == expected


class TestCaptlizePassthrough:
    @pytest.mark.parametrize(("text,passthrough,expected"), [
        ("text.' t ", ["'"], "text.' The "),
        ('text." t ', ["'"], 'text." the '),
        ('weird., hi ', [","], 'weird., Hi '),
        ('weir.d, hi ', [","], 'weir.d, hi '),

    ])
    def test_passthrough(self, text: str, passthrough: list[str], expected: str):
        override = _make_simple_override(
            {"rare": {"capitalize_passthrough": passthrough}})

        events = events_from_text(text)
        ctx = _process_events(events, override)

        assert_buff_equals(ctx, expected)


class TestNoSpaceOnNew:
    @pytest.mark.parametrize(("left", "right", "text", "expected"), [
        ("helloThere", "", "The ", "helloThereThe"),
        ("helloThere", "", "The  ", "helloThereThe "),
        ("helloThere", "Hi", "The ", "helloThereTheHi"),
        ("helloThere", "Hi", "The  ", "helloThereThe Hi"),
        ("hello_there_", "", "the ", "hello_there_the"),
        ("hello_there_", "", "the  ", "hello_there_the "),
    ])
    def test_proper_case(self, left, right, text, expected):
        ctx = _make_contextlr(
            left, right[::-1], _make_simple_override({"code": {"spacing_type": "new", "space_on_new": False}}), recent=False)
        events = events_from_text(text)
        _process_events(events, ctx=ctx)
        actual = ctx.buffers_to_str()
        assert actual == expected
