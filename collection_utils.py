def count_where(pred, iterable):
    count = 0
    for element in iterable:
        if pred(element):
            count += 1
    return count


def is_empty(iterable):
    return len(iterable) == 0


def captlize(s: str):
    if len(s) <= 1:
        return s.upper()

    return s[0].upper() + s[1:]
