import pytest
from collection_utils import (
    count_where,
    start_overlap_length,
    is_empty,
    is_empty_str,
    is_not_empty_str,
    ends_with_alnum,
    ends_with_any,
    starts_with_any,
    last_char,
    starts_with_alnum,
    no_overlap,
    toggle_captlize_word,
    toggle_all_caps,
    captlize,
    uncaptlize,
)


class TestCountWhere:
    @pytest.mark.parametrize(
        "pred,iterable,expected",
        [
            (lambda x: x > 2, [1, 2, 3, 4], 2),
            (lambda x: x == "a", ["a", "b", "a"], 2),
            (lambda x: len(x) > 3, ["a", "abc", "hello", "ab"], 1),
            (lambda x: False, [1, 2, 3], 0),
            (lambda x: True, [], 0),
        ],
    )
    def test_count_where(self, pred, iterable, expected):
        assert count_where(pred, iterable) == expected


class TestStartOverlapLength:
    @pytest.mark.parametrize(
        "s1,s2,expected",
        [
            ("hello", "hel", 3),
            ("abc", "abc", 3),
            ("xyz", "abc", 0),
            ("", "abc", 0),
            ("abc", "", 0),
            ("", "", 0),
            ("hello", "hello", 5),
            ("hel", "hello", 3),
            ("prefix", "prefix_suffix", 6),
        ],
    )
    def test_start_overlap_length(self, s1, s2, expected):
        assert start_overlap_length(s1, s2) == expected


class TestIsEmpty:
    @pytest.mark.parametrize(
        "iterable,expected",
        [
            ([], True),
            ([1], False),
            ("", True),
            ("a", False),
            ({}, True),
            ({"a": 1}, False),
        ],
    )
    def test_is_empty(self, iterable, expected):
        assert is_empty(iterable) == expected


class TestIsEmptyStr:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("", True),
            (" ", False),
            ("hello", False),
            ("\t", False),
        ],
    )
    def test_is_empty_str(self, s, expected):
        assert is_empty_str(s) == expected


class TestIsNotEmptyStr:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("", False),
            (" ", True),
            ("hello", True),
        ],
    )
    def test_is_not_empty_str(self, s, expected):
        assert is_not_empty_str(s) == expected


class TestEndsWithAlnum:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("hello", True),
            ("hello!", False),
            ("", False),
            ("a", True),
            ("123", True),
            ("abc123", True),
            (".", False),
            ("_", False),
        ],
    )
    def test_ends_with_alnum(self, s, expected):
        assert ends_with_alnum(s) == expected


class TestEndsWithAny:
    @pytest.mark.parametrize(
        "s,endings,expected",
        [
            ("hello", ["o", "l", "x"], True),
            ("hello", ["x", "y"], False),
            ("", ["a"], False),
            ("test.py", [".py", ".txt"], True),
            ("test", [".py"], False),
        ],
    )
    def test_ends_with_any(self, s, endings, expected):
        assert ends_with_any(s, endings) == expected


class TestStartsWithAny:
    @pytest.mark.parametrize(
        "s,starts,expected",
        [
            ("hello", ["h", "x"], True),
            ("hello", ["w", "x"], False),
            ("", ["a"], False),
            ("(test)", ["(", "[", "{"], True),
            ("test", ["("], False),
        ],
    )
    def test_starts_with_any(self, s, starts, expected):
        assert starts_with_any(s, starts) == expected


class TestLastChar:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("hello", "o"),
            ("a", "a"),
            ("", ""),
            (" ", " "),
        ],
    )
    def test_last_char(self, s, expected):
        assert last_char(s) == expected


class TestStartsWithAlnum:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("hello", True),
            ("1hello", True),
            ("", False),
            (" ", False),
            (".test", False),
            ("_test", False),
        ],
    )
    def test_starts_with_alnum(self, s, expected):
        assert starts_with_alnum(s) == expected


class TestNoOverlap:
    @pytest.mark.parametrize(
        "iter1,iter2,expected",
        [
            (["\t", "\n"], [" ", "x"], True),
            (["\t", "\n"], ["\t", "x"], False),
            (["a", "b"], ["c", "d"], True),
            (["a"], ["a"], False),
            ([], ["a"], True),
            (["a"], [], True),
        ],
    )
    def test_no_overlap(self, iter1, iter2, expected):
        assert no_overlap(iter1, iter2) == expected


class TestToggleCaptlizeWord:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("hello", "Hello"),
            ("", ""),
            ("a", "A"),
        ],
    )
    def test_toggle_captlize_word(self, s, expected):
        assert toggle_captlize_word(s) == expected


class TestToggleAllCaps:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("hello", "HELLO"),
            ("HELLO", "hello"),
            ("", ""),
        ],
    )
    def test_toggle_all_caps(self, s, expected):
        assert toggle_all_caps(s) == expected


class TestCaptlize:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("hello", "Hello"),
            ("h", "H"),
            ("HELLO", "HELLO"),
            ("", ""),
            ("a", "A"),
            ("ab", "Ab"),
        ],
    )
    def test_captlize(self, s, expected):
        assert captlize(s) == expected


class TestUncaptlize:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("Hello", "hello"),
            ("H", "h"),
            ("hello", "hello"),
            ("", ""),
            ("A", "a"),
            ("AB", "aB"),
        ],
    )
    def test_uncaptlize(self, s, expected):
        assert uncaptlize(s) == expected
