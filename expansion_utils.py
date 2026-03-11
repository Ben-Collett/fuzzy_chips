from frozen_dict import FrozenDict
from casing import Casing
from collection_utils import count_where,  captlize, is_not_empty_str
from typing import Optional
from utils import is_str
from config import Config
from functools import lru_cache


@lru_cache
def _upper_count(s: str) -> int:
    return sum(1 for c in s if c.isupper())


def empty_or_upper(s: str):
    return s == "" or s.isupper()
# this name kind of sucks


def _extract_ignored_leading_word_trailing(word: str, config):
    """
    extracts the leading characters, the word, and the trailing characters from the word variable based on the config
    ex:"'hello"', leading = "', word = hello, trailing = "', assuming that config.ignore_leading/trailing contain ' and "
    """
    ignored_leading = config.ignored_leading
    ignored_trailing = config.ignored_trailing

    leading = []
    trailing = []
    for ch in word:
        if ch in ignored_leading:
            leading.append(ch)
        else:
            break
    for ch in reversed(word):
        if ch in ignored_trailing:
            trailing.append(ch)
        else:
            break

    leading_str = "".join(leading)
    trailing_str = "".join(reversed(trailing))
    word = word.removeprefix(leading_str).removesuffix(trailing_str)
    return leading_str, word, trailing_str


def valid_chip(freq, config: Config):
    return freq in config.chip_map.keys()


def _update_captlization(word, upper_count: int):
    """updates the captlization based on upper_count, 1 = catplize, 1>uppercase, else no change"""
    if not is_str(word):
        return word
    if upper_count == 1:
        word = captlize(word)
    elif upper_count > 1:
        word = word.upper()
    return word


def get_chip_result(word: str, config: Config) -> list[str] | str | None:
    chip_map = config.chip_map
    char_frequency = FrozenDict.from_string(word)

    if valid_chip(char_frequency, config):
        return chip_map[char_frequency]

    def is_upper(ch): return ch.isupper()
    upper_count = count_where(is_upper, word)
    word = word.lower()
    char_frequency = FrozenDict.from_string(word)
    is_valid_chip = valid_chip(char_frequency, config)
    if is_valid_chip:
        chip = chip_map[char_frequency]
        return _update_captlization(chip, upper_count)

    leading, w, trailing = _extract_ignored_leading_word_trailing(
        word, config)
    char_frequency = FrozenDict.from_string(w)

    # we check if it's a str because if it is a list we don't handle ignoring leading and trailing
    # and if it got to this point we know it wasn't an exact match for a command chip
    is_valid_chip = valid_chip(char_frequency, config) and is_str(
        chip_map[char_frequency])
    if is_valid_chip:
        chip = chip_map[char_frequency]
        return leading+_update_captlization(chip, upper_count)+trailing

    return None


def _expand(word: str, config) -> str:
    out = get_chip_result(word, config)
    if out is None:
        out = word
    return out


def _last_capital_segment(s: str) -> str:
    """
    Returns the substring starting at the first capital letter.
    If no capital exists, returns the whole string.
    """
    for i in range(len(s)-1, 0, -1):
        if s[i].isupper():
            return s[i:]
    return s


def first_letter_is_upper(s: str):
    for ch in s:
        if ch.isalpha():
            return ch.isupper()
    return False


def get_casing_type(left_part: str, right_part: str) -> Casing:
    """
    tries to determine casing type
    from the contents to the left and right of the current curosr
    does not handle kebab case
    """

    # handles edgecase where variable separated by operator like hi_this= 2
    for ch in reversed(left_part):
        if not ch.isalnum() and ch != "_":
            return Casing.NORMAL
        elif ch.isalpha():
            break

    is_snake = "_" in left_part or "_" in right_part

    upper = left_part.isupper() and right_part.isupper()
    if is_snake and upper:
        return Casing.UPPER_SNAKE
    if is_snake:
        return Casing.SNAKE

    if empty_or_upper(left_part) and empty_or_upper(right_part):
        return Casing.NORMAL
    start_is_upper = first_letter_is_upper(left_part)

    count = _upper_count(left_part) + _upper_count(right_part)

    if start_is_upper:
        count -= 1
        if count > 0:
            return Casing.PROPER

    if count > 0:
        return Casing.CAMEL

    return Casing.NORMAL


def is_proper_case() -> bool:
    return False


def expand_snake_and_upper_snake_case(left_part: str, right_part: str, config: Config) -> (str, int):
    trail_count = 0
    for ch in reversed(left_part):
        early_exit = False
        if ch == "_":
            trail_count += 1
        if not ch.isalnum() and ch != "_":
            if trail_count == 1:
                early_exit = True
                break
        elif ch.isalpha():
            break

    # removes a single trailing underscore
    if trail_count == 1:
        return " ", 1
    # shouldn't expand
    if early_exit:
        return None, 0

    to_expand = None
    append = ""

    parts = left_part.split("_")
    to_expand = parts[-1] if parts else ""
    if not right_part.startswith("_"):
        append = "_"

    expanded = _expand(to_expand.lower(), config)

    # ASSUMING_UPPER_SNAKE_CASING
    if left_part.isupper() or right_part.isupper():
        expanded = expanded.upper()

    if expanded == to_expand:
        expanded = ""
        to_expand = ""

    out = expanded + append
    return list(out), len(to_expand)


def expand_cammel_and_proper_case(left_part: str, right_part: str, config: Config):
    luc = _upper_count(left_part)
    ruc = _upper_count(right_part)

    lf = _last_capital_segment(left_part)
    expanded = _expand(lf.lower(), config)

    upper_count = ruc+luc

    if len(lf) > 0 and lf[0].isupper():
        upper_count -= 1

    # assuming camelCase continuation
    if is_not_empty_str(right_part) and right_part[0].islower():
        return ["delete", *list(expanded), right_part[0].upper(), "left"], len(lf)

    # assuming ProperCase
    expanded = expanded[0].upper() + expanded[1:]
    if expanded == lf:
        return " ", 0
    return list(expanded), len(lf)


def expand_code_casing(left_part: str, right_part: str, config: Config) -> (Optional[str], int):
    casing = get_casing_type(left_part, right_part)

    to_write, count = None, 0
    if casing == Casing.SNAKE or casing == Casing.UPPER_SNAKE:
        to_write, count = expand_snake_and_upper_snake_case(
            left_part, right_part, config)
    elif casing == Casing.CAMEL or casing == Casing.PROPER:
        to_write, count = expand_cammel_and_proper_case(
            left_part, right_part, config)

    return to_write, count
