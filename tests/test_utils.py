import pytest
from utils import (
    compute_upper_count,
    is_str,
    is_all_non_alphanumeric_str,
    to_utf,
    alpha_numericish,
    backspaces_to_delete_previous_word,
)


class TestComputeUpperCount:
    def test_returns_zero_for_lowercase(self):
        assert compute_upper_count("hi there") == 0

    def test_returns_correct_count(self):
        assert compute_upper_count("hI tHeRe") == 3


class TestIsStr:
    def test_returns_true_for_string(self):
        assert is_str("hi")

    def test_returns_false_for_non_string(self):
        assert not is_str(["hi", "there"])


class TestIsAllNonAlphanumericStr:
    def test_returns_true_for_non_alphanumeric(self):
        assert is_all_non_alphanumeric_str("@)*! @#")

    def test_returns_true_for_empty(self):
        assert is_all_non_alphanumeric_str("")

    def test_returns_false_for_non_alphanumeric(self):
        assert not is_all_non_alphanumeric_str("@)*!1 @#")


class TestToUtf:
    @pytest.mark.parametrize("char,expected", [("h", "h"), ("b", "b")])
    def test_returns_lowercase_char(self, char, expected):
        assert to_utf(char, False) == expected

    @pytest.mark.parametrize("char,expected", [("h", "H"), ("b", "B")])
    def test_returns_uppercase_char_when_shift_down(self, char, expected):
        assert to_utf(char, True) == expected

    @pytest.mark.parametrize(
        "key,shift,expected",
        [
            ("space", False, " "),
            ("space", True, " "),
            ("tab", False, "\t"),
            ("enter", False, "\n"),
        ],
    )
    def test_special_keys(self, key, shift, expected):
        assert to_utf(key, shift) == expected

    def test_invalid_key(self):
        assert to_utf("blag", False) is None


class TestAlphaNumericish:
    @pytest.mark.parametrize("char", ["h", "2"])
    def test_returns_true_for_alphanumeric(self, char):
        assert alpha_numericish(char)

    def test_returns_true_for_apostrophe(self):
        assert alpha_numericish("'")

    @pytest.mark.parametrize("char", ['"', "(", "]", "="])
    def test_returns_false_for_other_chars(self, char):
        assert not alpha_numericish(char)


class TestBackspacesToDeletePreviousWord:
    def test_returns_one_for_empty_buffer(self):
        assert backspaces_to_delete_previous_word([""]) == 1

    def test_deletes_all_non_alphanumeric(self):
        assert backspaces_to_delete_previous_word(list(")()_(*&^'")) == 9

    @pytest.mark.parametrize(
        "buffer,expected",
        [
            ("", 0),
            ("hello", 5),
            ("Hello", 5),
            ("hello there ", 6),
            ("hello the", 3),
            ("hello The", 3),
            ("hello-the-thing", 5),
            ("hello-the-thing-", 6),
            ("Hello-The-Thing-", 6),
        ],
    )
    def test_natural_language(self, buffer, expected):
        assert backspaces_to_delete_previous_word(list(buffer)) == expected

    @pytest.mark.parametrize(
        "buffer,expected",
        [
            ("helloThereGood", 4),
            ("helloThereGood ", 5),
            ("HelloThereGood", 4),
            ("helloThereGood+", 5),
            ("helloThereGood(", 5),
            ("HelloThereGood(thing", 5),
            ("helloThereGood(ThingThe", 3),
            ("helloTHERE", 5),
            ("helloTHEREThat", 4),
        ],
    )
    def test_handles_camel_case(self, buffer, expected):
        assert backspaces_to_delete_previous_word(list(buffer)) == expected

    @pytest.mark.parametrize(
        "buffer,expected",
        [
            ("hello_", 6),
            ("hello_b", 1),
            ("hello_29", 2),
            ("hello_hat_thing", 5),
            ("hello_hat_thing(", 6),
             ("hello_hat_thing( ", 7),
            ("hello_hat_thing(person_that", 4),
            ("hello_hat_thing(person", 6),
        ],
    )
    def test_handles_snake_case(self, buffer, expected):
        assert backspaces_to_delete_previous_word(list(buffer)) == expected

    @pytest.mark.parametrize(
        "buffer,expected",
        [
            ("hello+hat+thing", 5),
            ("hello+hat+thing+", 6),
        ],
    )
    def test_handles_other_separators(self, buffer, expected):
        assert backspaces_to_delete_previous_word(list(buffer)) == expected
