from enum import Enum
from collection_utils import no_overlap, ends_with_any, starts_with_alnum
from collection_utils import ends_with_alnum, is_not_empty_str, starts_with_any
from collection_utils import captlize, uncaptlize, start_overlap_length, last_char
from utils import compute_upper_count
DASHES = {"\u002d",  # -
          "\u2010",  # hyphen
          "\u2011",  # non-breaking hyphen
          "\u2012",  # figure dash
          "\u2013",  # en dash
          "\u2014",  # em dash
          "\u2015",  # horizontal bar
          "\u2212",  # minus sign
          "\ufe58",  # small em dash
          "\uff0d",  # fullwidth hyphen-minus
          }


class Casing(Enum):
    NORMAL = "normal"
    KEBAB = "kebab"
    SNAKE = "snake"
    UPPER_SNAKE = "upper snake"
    CAMEL = "camel"
    PROPER = "proper"

    @property
    def is_normal_casing(self):
        return self == Casing.NORMAL

    @property
    def is_not_normal_casing(self):
        return self != Casing.NORMAL

    @staticmethod
    def safe_from_str(casing: str, default=NORMAL, generate_err_message=None):
        out = None
        try:
            out = Casing(casing)
        except ValueError:
            if generate_err_message:
                print(generate_err_message(casing, default))
            out = default

        return out


def is_dash(ch: str) -> bool:
    return ch in DASHES


def is_all_caps(s: str):
    """
    if a character is not upper/lower like a number it is treated
    as an a capitial, returns true for an empty string
    """
    for ch in s:
        if ch.islower():
            return False
    return True


def _first_letter_is_upper(s: str):
    for ch in s:
        if ch.isalpha():
            return ch.isupper()
    return False


def _upper_before_non_underscore_special(s, on_empty=False):
    length = 0
    for ch in s:
        length += 1
        if not ch.isalnum() and ch != "_":
            return False
        elif ch.isupper():
            return True
    out = on_empty
    if length > 0:
        out = False
    return out


def _upper_trailing_non_underscore_special(s: str, on_empty=False):
    return _upper_before_non_underscore_special(reversed(s), on_empty)


def _empty_or_upper(s: str):
    return s == "" or s.isupper()


def determine_code_casing(left_part: str, right_part: str, on_private_assume=Casing.SNAKE) -> Casing:
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

    # need to handle starting with _ sepratly because languages like dart
    # uses _ at the start of camel and propercasing
    is_likely_private = left_part.startswith("_")

    if left_part.startswith("_"):
        left_part = left_part[1:]
    is_snake = "_" in right_part or "_" in left_part

    if is_snake:
        print(left_part, right_part)
        left_upper = _upper_trailing_non_underscore_special(
            left_part, on_empty=True)
        print(left_upper)
        upper = left_upper and _upper_before_non_underscore_special(
            right_part, on_empty=True)
        if upper:
            return Casing.UPPER_SNAKE
        return Casing.SNAKE

    if _empty_or_upper(left_part) and _empty_or_upper(right_part):
        if is_likely_private and (left_part.isupper() or right_part.isupper()):
            return Casing.UPPER_SNAKE
        return Casing.NORMAL

    start_is_upper = _first_letter_is_upper(left_part)

    upper_count = compute_upper_count(
        left_part) + compute_upper_count(right_part)

    if start_is_upper:
        upper_count -= 1
        if upper_count > 0:
            return Casing.PROPER

    if upper_count > 0:
        return Casing.CAMEL

    if is_likely_private:
        return on_private_assume
    return Casing.NORMAL


def convert_casing(to_write, word, prev_word, prev_whitespace, casing: Casing):
    prepended = 0
    overlapping_start = 0
    if to_write == "":
        return "", overlapping_start, prepended

    # probably some form of field access if not in normal or kebab mode
    period_end = prev_word.endswith(".")
    period_start = word.startswith(".")
    open_end = ends_with_any(prev_word, ["(", '"', "'", '[', '{', '`'])
    close_end = ends_with_any(prev_word, [")", '"', "'", ']', '}', '`'])

    bracket_start = starts_with_any(word, ["(", ")", "[", "]", "{", "}"])

    alpha_numeric_end = ends_with_alnum(prev_word)
    alpha_numeric_start = starts_with_alnum(word)
    alpha_numeric_start_and_end = alpha_numeric_start and alpha_numeric_end

    # TODO: it might be nice to make this configurable
    has_prev_word = is_not_empty_str(prev_word)
    no_ws_overlap = no_overlap(["\t", "\n"], prev_whitespace)

    valid_start = alpha_numeric_start or period_start
    valid_end = period_end or alpha_numeric_end or open_end or close_end

    base_rule = has_prev_word and no_ws_overlap and valid_start and valid_end

    # for coding only
    bracket_rule = bracket_start or period_end

    should_prepend = base_rule or bracket_rule

    if casing == Casing.KEBAB and bracket_rule:
        should_prepend = False

    match casing:
        case Casing.NORMAL:
            overlapping_start = start_overlap_length(to_write, word)
        case Casing.KEBAB:
            to_write = to_write.replace(" ", "-")
            if period_end:
                to_write = captlize(to_write)

            if should_prepend:
                to_write = "-" + to_write

            should_prepend = should_prepend or is_dash(last_char(prev_word))
            if should_prepend:
                prepended = 1
        case Casing.SNAKE:
            to_write = to_write.lower()
            to_write = to_write.replace(" ", "_")
            if should_prepend and alpha_numeric_start_and_end:
                to_write = "_" + to_write
            if should_prepend or prev_word.endswith("_"):
                prepended = 1
        case Casing.UPPER_SNAKE:
            to_write = to_write.replace(" ", "_").upper()
            if should_prepend and alpha_numeric_start_and_end:
                to_write = "_" + to_write
            if should_prepend or prev_word.endswith("_"):
                prepended = 1
        case Casing.PROPER:
            to_write = captlize(to_write)
            # sometimes _ can denote being private
            if should_prepend or prev_word == "_":
                prepended = 1
        case Casing.CAMEL:
            to_write = "".join(map(captlize, to_write.split()))
            if period_end or open_end or not should_prepend:
                to_write = uncaptlize(to_write)

            # sometimes _ can denote being private
            if should_prepend or prev_word == "_":
                prepended = 1

    return to_write, prepended, overlapping_start
