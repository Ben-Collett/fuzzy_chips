import pytest
from casing import (
    Casing,
    is_dash,
    _first_letter_is_upper,
    _last_two_non_separators,
    _upper_before_non_underscore_special,
    _upper_trailing_non_underscore_special,
    _empty_or_upper,
    determine_code_casing,
    convert_casing,
)


class TestIsDash:
    @pytest.mark.parametrize(
        "ch,expected",
        [
            ("-", True),
            ("_", False),
            (" ", False),
            ("a", False),
        ],
    )
    def test_is_dash(self, ch, expected):
        assert is_dash(ch) == expected


class TestFirstLetterIsUpper:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("Hello", True),
            ("hello", False),
            ("", False),
            ("123abc", False),
            ("_hello", False),
        ],
    )
    def test_first_letter_is_upper(self, s, expected):
        assert _first_letter_is_upper(s) == expected


class TestLastTwoNonSeparators:
    @pytest.mark.parametrize(
        "word,expected",
        [
            ("", ("", "")),
            ("-", ("", "")),
            ("_", ("_", "")),
            ("hello", ("hello", "")),
            ("-hello", ("hello", "")),
            ("hello-", ("hello", "")),
            ("hello-there", ("there", "hello")),
            ("-hello-there-", ("there", "hello")),
            ("hello-there-world", ("world", "there")),
            ("hello.there", ("there", "hello")),
            ("hello.there.guy", ("guy", "there")),
            ("hello_there", ("hello_there", "")),
            ("hello_there-world", ("world", "hello_there")),
            ("hello-there_world", ("there_world", "hello")),
        ],
    )
    def test_last_two_non_separators(self, word, expected):
        assert _last_two_non_separators(word) == expected


class TestUpperBeforeNonUnderscoreSpecial:
    @pytest.mark.parametrize(
        "s,on_empty,expected",
        [
            ("HELLO", False, True),
            ("Hello", False, True),
            ("hello", False, False),
            ("", False, False),
            ("", True, True),
        ],
    )
    def test_upper_before_non_underscore_special(self, s, on_empty, expected):
        assert _upper_before_non_underscore_special(
            s, on_empty=on_empty) == expected


class TestUpperTrailingNonUnderscoreSpecial:
    @pytest.mark.parametrize(
        "s,on_empty,expected",
        [
            ("HELLO", False, True),
            ("Hello", False, True),
            ("hello", False, False),
            ("", False, False),
            ("", True, True),
        ],
    )
    def test_upper_trailing_non_underscore_special(self, s, on_empty, expected):
        assert _upper_trailing_non_underscore_special(
            s, on_empty=on_empty) == expected


class TestEmptyOrUpper:
    @pytest.mark.parametrize(
        "s,expected",
        [
            ("", True),
            ("_", False),
            ("_HI", False),
            ("HELLO", True),
            ("Hello", False),
            ("hello", False),
        ],
    )
    def test_empty_or_upper(self, s, expected):
        assert _empty_or_upper(s) == expected


class TestDetermineCodeCasing:
    @pytest.mark.parametrize(
        "left,right,expected",
        [
            ("hello", "", Casing.NORMAL),
            ("hello_world", "", Casing.SNAKE),
            ("HELLO_WORLD", "_there", Casing.SNAKE),
            ("HELLO_WORLD", "_THERE", Casing.UPPER_SNAKE),
            ("_private", "", Casing.SNAKE),
            ("hi=there", "", Casing.NORMAL),
            ("T", "", Casing.NORMAL),
            ("t-Th", "", Casing.NORMAL),
            ("hello", "_private", Casing.SNAKE),
            ('hello_there("the', "", Casing.NORMAL),
            ('hello_there(the', "", Casing.SNAKE),
            ('hello_there(23', "", Casing.NORMAL),
            ('hello_there(.', "", Casing.NORMAL),
            ('helloThere("the', "", Casing.NORMAL),
            ('helloThere(the', "", Casing.CAMEL),
            ('helloThere(_thing', "", Casing.CAMEL),
            ('helloThere(The', "", Casing.PROPER),
            ('HelloThere', "", Casing.PROPER),
            ('_HelloThere', "", Casing.PROPER),
            ('HelloThere(the', "", Casing.CAMEL),
            ('Hellothere(the', "", Casing.NORMAL),
            ('I.E.', "", Casing.NORMAL),
            ('i.e.', "", Casing.NORMAL),
            ('EX:', "", Casing.NORMAL),
            ('helloThere(23', "", Casing.NORMAL),
            ('helloThere(.', "", Casing.NORMAL),
        ],
    )
    def test_determine_code_casing(self, left, right, expected):
        assert determine_code_casing(left, right) == expected

    @pytest.mark.parametrize(
        "left,right,assumed_override,expected",
        [
            ("_private", "", Casing.SNAKE, Casing.SNAKE),
            ("_private", "", Casing.CAMEL, Casing.CAMEL),
            ("_private", "", Casing.KEBAB, Casing.KEBAB),
            ("_word", "var", Casing.PROPER, Casing.PROPER),
        ],
    )
    def test_determine_code_casing_on_private_assume(
        self, left, right, assumed_override, expected
    ):
        assert (
            determine_code_casing(
                left, right, on_private_assume=assumed_override)
            == expected
        )


class TestConvertCasing:
    @pytest.mark.parametrize(
        "to_write,word,prev_word,prev_whitespace,casing,expected",
        [
            ("hello", "hello", "", "", Casing.NORMAL, ("hello", 0, 5)),
            ("hello world", "hello", "", "", Casing.NORMAL, ("hello world", 0, 5)),
            ("hello world", "hello", "", "", Casing.KEBAB, ("hello-world", 0, 0)),
            ("hello world", "hello", "", "", Casing.SNAKE, ("hello_world", 0, 0)),
            ("hello world", "hello", "", "",
             Casing.UPPER_SNAKE, ("HELLO_WORLD", 0, 0)),
            ("hello world", "hello", "", "", Casing.PROPER, ("Hello world", 0, 0)),
            ("hello world", "hello", "", "", Casing.CAMEL, ("helloWorld", 0, 0)),
        ],
    )
    def test_convert_casing(
        self, to_write, word, prev_word, prev_whitespace, casing, expected
    ):
        result = convert_casing(
            to_write, word, prev_word, prev_whitespace, casing)
        assert result == expected

    def test_convert_casing_empty_to_write(self):
        result = convert_casing("", "word", "prev", " ", Casing.NORMAL)
        assert result == ("", 0, 0)
