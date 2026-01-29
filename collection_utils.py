def count_where(pred, iterable):
    count = 0
    for element in iterable:
        if pred(element):
            count += 1
    return count


def start_overlap_length(s1: str, s2: str):
    length = 0
    short_length = min(len(s1), len(s2))
    for i in range(0, short_length):
        if s1[i] != s2[i]:
            break
        length += 1
    return length


def is_empty(iterable):
    return len(iterable) == 0


def is_empty_str(s: str):
    return s == ""


def is_not_empty_str(s: str):
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


def captlize(s: str):
    if len(s) <= 1:
        return s.upper()

    return s[0].upper() + s[1:]


def uncaptlize(s: str):
    if len(s) <= 1:
        return s.lower()

    return s[0].lower() + s[1:]
