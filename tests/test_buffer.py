import pytest
from buffer import BufferEntry, KeyBuffer


class TestBufferEntry:
    def test_creation(self):
        entry = BufferEntry("a", True)
        assert entry.char == "a"
        assert entry.recent is True


class TestKeyBuffer:
    def test_initialization(self):
        buf = KeyBuffer(5)
        assert buf.capacity == 5
        assert buf.is_empty()

    def test_add_and_get(self):
        buf = KeyBuffer(5)
        buf.add("h")
        buf.add("i")
        assert buf.get() == ["h", "i"]

    def test_add_all(self):
        buf = KeyBuffer(10)
        buf.add_all("hello")
        assert buf.get() == ["h", "e", "l", "l", "o"]

    def test_add_all_recent_false(self):
        buf = KeyBuffer(10)
        buf.add_all("hello", recent=False)
        entries = list(buf.buffer)
        assert buf.get() == ["h", "e", "l", "l", "o"]
        assert all(e.recent is False for e in entries)

    def test_add_with_recent_flag(self):
        buf = KeyBuffer(5)
        buf.add("a", recent=True)
        buf.add("b", recent=False)
        entries = list(buf.buffer)
        assert entries[0].recent is True
        assert entries[1].recent is False

    def test_capacity_enforcement(self):
        buf = KeyBuffer(3)
        buf.add_all("abcdef")
        assert len(buf) == 3
        assert buf.get() == ["d", "e", "f"]

    def test_clear(self):
        buf = KeyBuffer(5)
        buf.add_all("abc")
        buf.clear()
        assert buf.is_empty()

    def test_set_buffer(self):
        buf = KeyBuffer(10)
        buf.set_buffer("hello")
        assert buf.get() == ["h", "e", "l", "l", "o"]

    def test_set_buffer_recent_false(self):
        buf = KeyBuffer(10)
        buf.set_buffer("hello", recent=False)
        assert buf.get() == ["h", "e", "l", "l", "o"]
        entries = list(buf.buffer)
        assert all(e.recent is False for e in entries)

    def test_set_buffer_recent_true_explicit(self):
        buf = KeyBuffer(10)
        buf.set_buffer("hi", recent=True)
        entries = list(buf.buffer)
        assert all(e.recent is True for e in entries)

    def test_is_equal(self):
        buf = KeyBuffer(5)
        buf.add_all("hello")
        assert buf.is_equal("hello")
        assert not buf.is_equal("world")

    def test_backspace(self):
        buf = KeyBuffer(5)
        buf.add_all("ab")
        char = buf.backspace()
        assert char == "b"
        assert buf.get() == ["a"]

    def test_backspace_entry(self):
        buf = KeyBuffer(5)
        buf.add("x", recent=False)
        entry = buf.backspace_entry()
        assert entry.char == "x"
        assert entry.recent is False

    def test_backspace_empty_buffer(self):
        buf = KeyBuffer(5)
        assert buf.backspace() is None
        assert buf.backspace_entry() is None

    def test_remove_first(self):
        buf = KeyBuffer(5)
        buf.add_all("abc")
        buf.remove_first()
        assert buf.get() == ["b", "c"]

    def test_remove_first_empty(self):
        buf = KeyBuffer(5)
        buf.remove_first()
        assert buf.is_empty()

    def test_mark_recent_as_old(self):
        buf = KeyBuffer(5)
        buf.add("a", recent=True)
        buf.add("b", recent=True)
        buf.mark_recent_as_old()
        entries = list(buf.buffer)
        assert entries[0].recent is False
        assert entries[1].recent is False

    def test_get_word_entries_positive_index(self):
        buf = KeyBuffer(20)
        buf.set_buffer("hello world test", recent=False)
        entries = buf.get_word_entries(0)
        assert "".join(e.char for e in entries) == "hello"
        entries = buf.get_word_entries(1)
        assert "".join(e.char for e in entries) == "world"
        entries = buf.get_word_entries(2)
        assert "".join(e.char for e in entries) == "test"

    def test_get_word_entries_negative_index(self):
        buf = KeyBuffer(20)
        buf.set_buffer("hello world test", recent=False)
        entries = buf.get_word_entries(-1)
        assert "".join(e.char for e in entries) == "test"
        entries = buf.get_word_entries(-2)
        assert "".join(e.char for e in entries) == "world"

    def test_get_word_entries_out_of_range(self):
        buf = KeyBuffer(20)
        buf.set_buffer("hello", recent=False)
        assert buf.get_word_entries(5) == []
        assert buf.get_word_entries(-10) == []

    def test_get_word_entries_empty_buffer(self):
        buf = KeyBuffer(5)
        assert buf.get_word_entries(0) == []

    def test_get_word(self):
        buf = KeyBuffer(20)
        buf.set_buffer("hello world", recent=False)
        assert buf.get_word(0) == "hello"
        assert buf.get_word(1) == "world"
        assert buf.get_word(-1) == "world"

    def test_get_word_and_new_state(self):
        buf = KeyBuffer(20)
        buf.add("h", recent=True)
        buf.add("e", recent=True)
        buf.add("l", recent=False)
        buf.add("l", recent=False)
        buf.add("o", recent=False)
        word, is_new = buf.get_word_and_new_state(0)
        assert word == "hello"
        assert is_new == [True, True, False, False, False]

    def test_get_leading_white_space(self):
        buf = KeyBuffer(20)
        buf.set_buffer("  hello")
        assert buf.get_leading_white_space() == "  h"

    def test_get_leading_white_space_no_space(self):
        buf = KeyBuffer(20)
        buf.set_buffer("hello")
        assert buf.get_leading_white_space() == ""

    def test_get_trailing_white_space(self):
        buf = KeyBuffer(20)
        buf.set_buffer("hello  ")
        assert buf.get_trailing_white_space() == "  "

    def test_get_trailing_white_space_no_space(self):
        buf = KeyBuffer(20)
        buf.set_buffer("hello")
        assert buf.get_trailing_white_space() == ""

    def test_get_white_space_before_prev_word(self):
        buf = KeyBuffer(20)
        buf.set_buffer("hello  world")
        assert buf.get_white_space_before_prev_word() == "  "

    def test_get_white_space_before_prev_word_no_prev(self):
        buf = KeyBuffer(20)
        buf.set_buffer("hello ")
        assert buf.get_white_space_before_prev_word() == ""

    def test_get_last_word(self):
        buf = KeyBuffer(20)
        buf.set_buffer("hello world test")
        assert buf.get_last_word() == "test"

    def test_str_representation(self):
        buf = KeyBuffer(5)
        buf.add_all("abc")
        assert str(buf) == "['a', 'b', 'c']"

    def test_is_empty(self):
        buf = KeyBuffer(5)
        assert buf.is_empty() is True
        buf.add("x")
        assert buf.is_empty() is False

    def test_len(self):
        buf = KeyBuffer(5)
        assert len(buf) == 0
        buf.add_all("abc")
        assert len(buf) == 3


class TestShouldCaptilizePrevWord:
    def test_capitalize_after_period(self):
        buf = KeyBuffer(20)
        buf.set_buffer("hello. world")
        assert buf.should_captlize_prev_word(captilize_after=["."]) is True

    def test_no_capitalize_after_non_match(self):
        buf = KeyBuffer(20)
        buf.set_buffer("hello, world")
        assert buf.should_captlize_prev_word(captilize_after=["."]) is False

    def test_returns_false_for_empty_buffer(self):
        buf = KeyBuffer(5)
        assert buf.should_captlize_prev_word(captilize_after=["."]) is False

    def test_returns_false_when_no_prev_word(self):
        buf = KeyBuffer(20)
        buf.set_buffer(" hello")
        assert buf.should_captlize_prev_word(captilize_after=["."]) is False

    def test_pass_through(self):
        buf = KeyBuffer(20)
        buf.set_buffer("hello ( world")
        assert (
            buf.should_captlize_prev_word(captilize_after=["."], pass_through=["("])
            is False
        )
