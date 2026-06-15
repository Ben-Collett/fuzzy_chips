def count_where(pred, iterable):
    count = 0
    for element in iterable:
        if pred(element):
            count += 1
    return count


def list_get_or_default(lst: list, index: int, default) -> list:
    try:
        return lst[index]
    except IndexError:
        return default


def start_overlap_length(a: str, b: str):
    count = 0
    for ch1, ch2 in zip(a, b):
        if ch1 != ch2:
            break
        count += 1
    return count


def is_empty(iterable):
    return len(iterable) == 0


def is_empty_str(s: str):
    return s == ""


def is_not_empty_str(s):
    return s != ""


def ends_with_alnum(s: str) -> bool:
    if not s or is_empty_str(s):
        return False
    return s[-1].isalnum()


def ends_with_any(s: str, endings):
    for ending in endings:
        if s.endswith(ending):
            return True
    return False


def starts_with_any(s: str, starts):
    for start in starts:
        if s.startswith(start):
            return True
    return False


def last_char(s: str):
    if len(s) < 1:
        return ""
    return s[-1]


def starts_with_alnum(s: str) -> bool:
    if not s or is_empty_str(s):
        return False
    return s[0].isalnum()


def no_overlap(iter1, iter2):
    seen = set()

    for val in iter1:
        seen.add(val)

    for val in iter2:
        if val in seen:
            return False
    return True


def toggle_captlize_word(s: str) -> str:
    index = 0
    length = len(s)
    while index < length:
        if s[index].isalpha():
            break
        index += 1
    if index == length:
        return s

    if s[index].islower():
        return s[:index]+captlize_first_char(s[index:])
    return s[:index]+uncaptlize_first_char(s[index:])


def toggle_all_caps(s: str):
    if s.islower():
        return s.upper()
    return s.lower()


def captlize_first_char(s: str):
    if len(s) <= 1:
        return s.upper()

    return s[0].upper() + s[1:]


def uncaptlize_first_char(s: str):
    if len(s) <= 1:
        return s.lower()

    return s[0].lower() + s[1:]


def captlize_word(s: str):
    index = 0
    length = len(s)
    while index < length:
        if s[index].isalpha():
            break
        index += 1
    if index == length:
        return s

    return s[:index] + s[index].upper() + s[index+1:]
