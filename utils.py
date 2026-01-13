def alpha_numericish(ch: str):
    return ch.isalnum() or ch == "'"


def backspaces_to_delete_previous_word(buffer: list[str]) -> int:
    if not buffer:
        return 0

    i = len(buffer) - 1
    count = 0

    while i >= 0 and not buffer[i].isalnum():
        count += 1
        i -= 1

    if i < 0:
        return len(buffer) - i

    upper_mode = buffer[i].isupper()

    if upper_mode:
        while i > 0:
            i -= 1
            count += 1
            ch = buffer[i]
            if ch.islower() or ch.isspace():
                return count-1
            if not alpha_numericish(ch):
                return count
    else:
        while i > 0:
            i -= 1
            count += 1
            ch = buffer[i]
            if ch.isspace():
                return count-1
            if ch.isupper() or not alpha_numericish(ch):
                return count

    return len(buffer) - 1
