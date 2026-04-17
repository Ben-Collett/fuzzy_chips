import pytest
from unittest.mock import MagicMock
from frozen_dict import FrozenDict
from expansion_utils import (
    _partition_non_alnum_edges,
    is_valid_chip_str,
    valid_chip,
    _update_captlization,
    _last_capital_segment,
    _last_snake_part,
    starts_with_alnum,
    expand_snake_and_upper_snake_case,
    expand_cammel_and_proper_case,
    _split_last_token,
    shift_press_release,
    expand_code_casing,
    split_new_part,
    _ends_with_alpha_numeric,
    _starts_with_lower,
    _starts_with_upper,
    expand_new,
    expand_chunking,
)
from casing import Casing
from chunking import ChunkingType


class TestExtractIgnoredLeadingWordTrailing:

    @pytest.mark.parametrize(
        "word,expected",
        [
            ("hello", ("", "hello", "")),
            ("hello world", ("", "hello world", "")),
        ],
    )
    def test_extract_ignored(self, word, expected):
        result = _partition_non_alnum_edges(word)
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
        result = split_new_part(s, flags)
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


class TestExpandChunking:
    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        fd = FrozenDict.from_string("hi")
        config.chip_map = {fd: "hello"}
        config.chunking_ignore = ["_"]
        config.chunking_type = ChunkingType.ALL
        config.new_chunks_only = False
        return config

    @pytest.fixture
    def mock_config_last(self):
        config = MagicMock()
        fd = FrozenDict.from_string("hi")
        config.chip_map = {fd: "hello"}
        config.chunking_ignore = ["_"]
        config.chunking_type = ChunkingType.LAST
        config.new_chunks_only = False
        return config

    @pytest.fixture
    def mock_config_new_chunks(self):
        config = MagicMock()
        fd = FrozenDict.from_string("hi")
        config.chip_map = {fd: "hello"}
        config.chunking_ignore = ["_"]
        config.chunking_type = ChunkingType.LAST
        config.new_chunks_only = True
        return config

    def test_expand_chunking_all_type_expands_all_chunks(self, mock_config):
        result = expand_chunking("hi hello", [True, True, True, True, True, True, True, True], mock_config)
        assert result == "hello hello"

    def test_expand_chunking_all_type_no_expansion(self, mock_config):
        result = expand_chunking("abc def", [True, True, True, True, True, True], mock_config)
        assert result == "abc def"

    def test_expand_chunking_all_type_with_separators(self, mock_config):
        result = expand_chunking("hi-hello", [True, True, True, True, True, True], mock_config)
        assert result == "hello-hello"

    def test_expand_chunking_all_type_expansion_returns_list(self, mock_config):
        def mock_expand(val, config):
            if val == "hi":
                return ["delete", "h", "i"]
            return val
        mock_config.chunking_type = ChunkingType.ALL
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("expansion_utils._expand", mock_expand)
            result = expand_chunking("hi", [True, True], mock_config)
            assert result == "hi"

    def test_expand_chunking_last_type_expands_last_only(self, mock_config_last):
        result = expand_chunking("hi hello", [True, True, True, True, True, True, True, True], mock_config_last)
        assert result == "hi hello"

    def test_expand_chunking_last_type_no_expansion(self, mock_config_last):
        result = expand_chunking("abc def", [True, True, True, True, True, True], mock_config_last)
        assert result == "abc def"

    def test_expand_chunking_last_type_with_separators(self, mock_config_last):
        result = expand_chunking("hi-hello", [True, True, True, True, True, True], mock_config_last)
        assert result == "hi-hello"

    def test_expand_chunking_with_ignored_chars(self, mock_config):
        result = expand_chunking("hi-hello", [True, True, True, True, True, True, True, True], mock_config)
        assert result == "hello-hello"

    def test_expand_chunking_new_chunks_only_with_old_part(self, mock_config_new_chunks):
        result = expand_chunking("abchi", [False, False, False, True, True], mock_config_new_chunks)
        assert result == "abchi"

    def test_expand_chunking_new_chunks_only_all_new(self, mock_config_new_chunks):
        result = expand_chunking("hi", [True, True], mock_config_new_chunks)
        assert result == "hello"

    def test_expand_chunking_new_chunks_only_empty_new_part(self, mock_config_new_chunks):
        result = expand_chunking("abc", [False, False, False], mock_config_new_chunks)
        assert result == "abc"

    def test_expand_chunking_empty_input(self, mock_config):
        result = expand_chunking("", [], mock_config)
        assert result == ""

    def test_expand_chunking_mixed_expansion_and_not(self, mock_config):
        result = expand_chunking("hi abc", [True, True, True, True, True, True], mock_config)
        assert result == "hello abc"
