import pytest
from unittest.mock import MagicMock
from frozen_dict import FrozenDict
from expansion_utils import (
    _extract_ignored_leading_word_trailing,
    is_valid_chip_str,
    valid_chip,
    _update_captlization,
    get_chip_result,
    _last_capital_segment,
    _last_snake_part,
    starts_with_alnum,
    expand_snake_and_upper_snake_case,
    expand_cammel_and_proper_case,
    _split_last_token,
    shift_press_release,
    expand_code_casing,
    _split_new_part,
    _safe_char_check,
    _ends_with_alpha_numeric,
    _starts_with_alpha_numeric,
    _starts_with_lower,
    _starts_with_upper,
    expand_new,
)
from casing import Casing


class TestExtractIgnoredLeadingWordTrailing:
    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.ignored_leading = ['"', "'", "("]
        config.ignored_trailing = ['"', ")", "]"]
        return config

    @pytest.mark.parametrize(
        "word,expected",
        [
            ("hello", ("", "hello", "")),
            ("hello world", ("", "hello world", "")),
        ],
    )
    def test_extract_ignored(self, mock_config, word, expected):
        result = _extract_ignored_leading_word_trailing(word, mock_config)
        assert result == expected


class TestIsValidChipStr:
    def test_is_valid_chip_str_true(self):
        config = MagicMock()
        fd = FrozenDict.from_string("hi")
        config.chip_map = {fd: "hello"}
        assert is_valid_chip_str("hi", config) is True

    def test_is_valid_chip_str_false(self):
        config = MagicMock()
        fd = FrozenDict.from_string("hi")
        config.chip_map = {}
        assert is_valid_chip_str("hi", config) is False


class TestValidChip:
    def test_valid_chip_true(self):
        config = MagicMock()
        fd = FrozenDict.from_string("hi")
        config.chip_map = {fd: "hello"}
        assert valid_chip(fd, config) is True

    def test_valid_chip_false(self):
        config = MagicMock()
        fd = FrozenDict.from_string("hi")
        config.chip_map = {}
        assert valid_chip(fd, config) is False


class TestUpdateCaptlization:
    @pytest.mark.parametrize(
        "word,upper_count,expected",
        [
            ("hello", 0, "hello"),
            ("hello", 1, "Hello"),
            ("hello", 2, "HELLO"),
            ("", 1, ""),
            ("a", 1, "A"),
            (123, 1, 123),
            (["list"], 1, ["list"]),
        ],
    )
    def test_update_captlization(self, word, upper_count, expected):
        result = _update_captlization(word, upper_count)
        assert result == expected


class TestLastCapitalSegment:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("helloWorld", "World"),
            ("HelloWorld", "World"),
            ("_Private", "Private"),
        ],
    )
    def test_last_capital_segment(self, s, expected):
        assert _last_capital_segment(s) == expected


class TestLastSnakePart:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("hello_world", "world"),
            ("hello", "hello"),
            ("", ""),
        ],
    )
    def test_last_snake_part(self, s, expected):
        assert _last_snake_part(s) == expected


class TestStartsWithAlnum:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("hello", True),
            ("1test", True),
            ("", False),
            (" ", False),
            (".test", False),
            ("_test", False),
        ],
    )
    def test_starts_with_alnum(self, s, expected):
        assert starts_with_alnum(s) == expected


class TestExpandSnakeAndUpperSnakeCase:
    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.space_on_new = True
        return config

    def test_expand_snake_trailing_underscore(self, mock_config):
        result = expand_snake_and_upper_snake_case(
            "hello_", "world", Casing.SNAKE, mock_config
        )
        assert result == ([" "], 1)


class TestExpandCammelAndProperCase:
    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        return config

    def test_expand_cammel_case(self, mock_config):
        result = expand_cammel_and_proper_case("Hello", "World", mock_config)
        assert result[0] == [" "]


class TestSplitLastToken:
    def test_split_last_token_simple(self):
        result = _split_last_token("hello")
        assert result == ("", "hello")


class TestShiftPressRelease:
    def test_shift_press_release_simple(self):
        result = shift_press_release("hello", " ")
        assert result[0] > 0


class TestExpandCodeCasing:
    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.space_on_new = True
        return config

    def test_expand_snake_code_casing(self, mock_config):
        result = expand_code_casing("hello", "world", Casing.SNAKE, mock_config)
        assert result[0] == ["_"]


class TestSplitNewPart:
    @pytest.mark.parametrize(
        "s,flags,expected",
        [
            ("", [], ("", "")),
        ],
    )
    def test_split_new_part(self, s, flags, expected):
        result = _split_new_part(s, flags)
        assert result == expected


class TestEndsWithAlphaNumeric:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("hello", True),
            ("hello!", False),
            ("", False),
            ("123", True),
        ],
    )
    def test_ends_with_alpha_numeric(self, s, expected):
        assert _ends_with_alpha_numeric(s) == expected


class TestStartsWithAlphaNumeric:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("hello", True),
            ("1test", True),
            ("", False),
            ("!test", False),
        ],
    )
    def test_starts_with_alpha_numeric(self, s, expected):
        assert _starts_with_alpha_numeric(s) == expected


class TestStartsWithLower:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("hello", True),
            ("Hello", False),
            ("", False),
        ],
    )
    def test_starts_with_lower(self, s, expected):
        assert _starts_with_lower(s) == expected


class TestStartsWithUpper:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("Hello", True),
            ("hello", False),
            ("", False),
        ],
    )
    def test_starts_with_upper(self, s, expected):
        assert _starts_with_upper(s) == expected


class TestExpandNew:
    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.assumed_casing = Casing.SNAKE
        config.space_on_new = True
        return config

    def test_expand_new_empty_left(self, mock_config):
        result = expand_new("", [], " ", "test", mock_config)
        assert result == (None, 0)

    def test_expand_new_multiple_spaces(self, mock_config):
        result = expand_new("hello", [True] * 5, "  ", "world", mock_config)
        assert result == (None, 0)
