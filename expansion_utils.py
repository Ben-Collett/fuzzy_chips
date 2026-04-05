from frozen_dict import FrozenDict
from casing import Casing, determine_code_casing
from collection_utils import count_where,  captlize, is_not_empty_str
from collection_utils import toggle_all_caps, toggle_captlize_word
from typing import Optional
from utils import is_str, compute_upper_count, reverse_enumerate
from utils import reversed_range, is_str
from config import Config


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


def is_valid_chip_str(s: str, config: Config):
    return valid_chip(FrozenDict.from_string(s), config)


def valid_chip(freq: FrozenDict, config: Config):
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


def _last_snake_part(left_part):
    parts = left_part.split("_")
    last_part = parts[-1] if parts else ""
    return last_part


def starts_with_alnum(s: str):
    return is_not_empty_str(s) and s[0].isalnum()


def expand_snake_and_upper_snake_case(left_part: str, right_part: str, casing: Casing, config: Config, force_prepend="", remove_trailing=True) -> (list[str], int):
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
    # if to or more underscores don't remove but space forward
    if remove_trailing and trail_count == 1:
        return [" "], 1
    elif trail_count >= 1:
        if config.space_on_new:
            return [" "], 0
        else:
            return [], 0

    # shouldn't expand
    if early_exit:
        return [], 0

    to_expand = _last_snake_part(left_part)
    append = ""

    if starts_with_alnum(right_part):
        append = "_"

    expanded = _expand(to_expand.lower(), config)

    if casing == Casing.UPPER_SNAKE:
        expanded = expanded.upper()

    expanded = force_prepend+expanded

    if expanded == to_expand:
        expanded = ""
        to_expand = ""
    out = expanded + append
    if out == "" and right_part.startswith("_"):
        return [" "], 0
    return list(out), len(to_expand)


def expand_cammel_and_proper_case(left_part: str, right_part: str, config: Config, force_proper=False, space_on_no_change=True) -> (list[str], int):
    """
    returns to write, the amount to backspace, and if the expansion output was a list.
    """
    luc = compute_upper_count(left_part)
    ruc = compute_upper_count(right_part)

    private = left_part.startswith("_")
    if private:
        left_part = left_part[1:]

    lf = _last_capital_segment(left_part)
    expanded = _expand(lf.lower(), config)

    upper_count = ruc+luc

    if len(lf) > 0 and lf[0].isupper():
        upper_count -= 1

    if not is_str(expanded):
        return expanded, len(lf)

    if force_proper or _starts_with_upper(left_part) or len(lf) < len(left_part):
        expanded = expanded[0].upper() + expanded[1:]

    if _starts_with_lower(right_part):
        return ["delete", *list(expanded), right_part[0].upper(), "left"], len(lf)

    if expanded == lf:
        if space_on_no_change:
            return [" "], 0
        else:
            return [], 0

    return list(expanded), len(lf)


def _split_last_token(s: str) -> (str, str):
    """
    Return the last word-like token in `s`.

    A token is made of alphanumerics, `_`, or `'`.
    Trailing separators are ignored.
    """
    # one character past the last non alpha/_/' character
    tmp_index = 0
    # used to not trigger for leading break characters ex. hi-there- will grab there-
    is_trailing = True
    for i, ch in reverse_enumerate(s):

        is_break_char = not (ch.isalnum() or ch == "_" or ch == "'")
        if not is_trailing and is_break_char:
            tmp_index = i+1  # skip the break character
            break

        if not is_break_char:
            is_trailing = False

    return s[:tmp_index], s[tmp_index:]


def shift_press_release(word: str, trailing_white_space: str) -> (int, str):
    """
    left word -> the word at the end of the main buffer
    trailing_space->space between that word and the end


    this is cool -> nothing special captlize prev word or current word
    EX: this is cool -> this is Cool
    this-is-cool -> stop when you hit a nonspecial non _ character and captlize thefirst letter of that word(last thing in stack)
    EX: this-is-cool-> this-is-Cool
    hat=dog, captlize dog because non-alpha sperator rule same with hat+dog
    EX: hot=dog -> hot=Dog
    thisIsCool -> same rulse as normal case and separator should cover this case aswell
    EX: thisIsCool -> ThisIsCool
    hot_dog-> if we hit _ stop and next special character or " ", swap case of whatever came before all upp or all down
    with the exception of a starting _ so that things like dart private scope works nicely.
    EX: hot_dog -> HOT_DOG -> hot_dog, _randomDog -> _RandomDog->_randomDog, _hot_dog -> _HOT_DOG

    if it is split on a - or + or something toggle only the last word
    simple rule, get last word if it contains _ as first alpha numeric toggle the whole word
    unless it is just at the start
    if there is only one word or it's just a space or camel toggle the case of the first letter
    """

    _, word = _split_last_token(word)
    leading_underscore = word.startswith("_")
    if leading_underscore:
        word = word[1:]

    is_snake_case = "_" in word
    if is_snake_case:
        word = toggle_all_caps(word)
    else:
        word = toggle_captlize_word(word)

    if leading_underscore:
        word = "_"+word
    word += trailing_white_space

    return len(word), word


def expand_code_casing(left_part: str, right_part: str, casing: Casing, config: Config) -> (Optional[list[str]], int):
    to_write, count = None, 0
    if casing == Casing.SNAKE or casing == Casing.UPPER_SNAKE:
        to_write, count = expand_snake_and_upper_snake_case(
            left_part, right_part, casing, config)
    elif casing == Casing.CAMEL or casing == Casing.PROPER:
        to_write, count = expand_cammel_and_proper_case(
            left_part, right_part, config)

    return to_write, count


def _get_old_and_new_part(word: str, new_flags: list[bool]) -> (str, str):
    index = 0
    for i, is_new in reverse_enumerate(new_flags):
        if not is_new:
            index = i
            break

    return word[0:index], word[index:]


def _split_new_part(s: str, new_flags: list[bool]) -> (str, str):
    if len(s) == 0:
        return "", ""
    index = 0
    for i in reversed_range(s):
        if not new_flags[i]:
            index = i+1
            break

    return s[0:index], s[index:]


def _safe_char_check(s: str, index: int, check):
    return bool(s) and check(s[index])


def _ends_with_alpha_numeric(s: str):
    return _safe_char_check(s, -1, str.isalnum)


def _starts_with_alpha_numeric(s: str):
    return _safe_char_check(s, 0, str.isalnum)


def _starts_with_lower(s: str):
    return _safe_char_check(s, 0, str.islower)


def _starts_with_upper(s: str):
    return _safe_char_check(s, 0, str.isupper)


def expand_new(left_part: str, new_flags: list[bool], white_space: str, right_part: str, config: Config) -> (list[str], int):

    if len(left_part) == 0 or len(white_space) > 1:
        return None, 0

    assert len(left_part) == len(
        new_flags), f'length miss match should be impossible:{len(left_part)=}, {len(new_flags)=}'

    to_write, count = None, 0

    assumed_casing = config.assumed_casing
    casing = determine_code_casing(
        left_part, right_part, on_private_assume=assumed_casing)
    print(casing)
    if casing == Casing.NORMAL:
        casing = assumed_casing

    if casing == Casing.NORMAL:
        return None, 0

    old_part, new_part = _split_new_part(left_part, new_flags)

    # print(new_part, left_part, new_flags)
    if new_part == "":
        return None, 0
    print(casing)

    tmp, new_part = _split_last_token(new_part)
    old_part += tmp

    print(casing)
    if casing == Casing.SNAKE or casing == Casing.UPPER_SNAKE:

        force_prpend = ""
        if _ends_with_alpha_numeric(old_part) and not new_part.startswith("_"):
            force_prpend = "_"

        print(casing)
        to_write, count = expand_snake_and_upper_snake_case(
            new_part, right_part, casing, config, force_prpend, remove_trailing=False)

    force_upper = _ends_with_alpha_numeric(
        old_part) or _starts_with_upper(right_part)
    if casing == Casing.PROPER:
        force_upper = True
        casing = Casing.CAMEL

    if casing == Casing.CAMEL:
        to_write, count = expand_cammel_and_proper_case(
            new_part, right_part, config, force_proper=force_upper, space_on_no_change=config.space_on_new)

    return to_write, count
