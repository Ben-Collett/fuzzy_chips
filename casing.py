from enum import Enum
from collection_utils import no_overlap, ends_with_any, starts_with_alnum
from collection_utils import ends_with_alnum, is_not_empty_str, starts_with_any
from collection_utils import captlize, uncaptlize, start_overlap_length, last_char
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
    NORMAL = "normal",
    KEBAB = "kebab"
    SNAKE = "snake"
    UPPER_SNAKE = "upper snake"
    CAMEL = "cammel"
    PROPER = "proper"


def is_dash(ch: str) -> bool:
    return ch in DASHES


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
