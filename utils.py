from collections import deque


def alpha_numericish(ch: str):
    return ch.isalnum() or ch == "'"


"""
hot_dog=cat_pig if we hit _ stop and next special character or " ", swap case of whatever came before all upp or all down
this is cool -> nothing special captlize prev word or current word
this-is-cool -> stop when you hit a nonspecial non _ character and captlize thefirst letter of that word(last thing in stack)
hat=dog, captlize dog because non-alpha sperator rule same with hat+dog
thisIsCool -> same rulse as normal case and separator should cover this case aswell

if it is split on a - or + or something toggle only the last word
simple rule, get last word if it contains _ as first alpha numeric toggle the whole word
if there is only one word or it's just a space or camel toggle the case of the first letter
"""


def shift_press_release(buffer: list[str]) -> (int, str):

    if not buffer:
        return 0, ""

    queue = deque()
    i = len(buffer) - 1
    backspace_count = 0

    while i >= 0 and not buffer[i].isalnum():
        queue.appendleft(buffer[i])
        backspace_count += 1
        i -= 1

    toggle_whole_word = False
    while i >= 0 and buffer[i] != " ":
        if buffer[i] == "_":
            toggle_whole_word = True
        elif not buffer[i].isalnum():
            break

        backspace_count += 1
        queue.appendleft(buffer[i])
        i -= 1

    if toggle_whole_word:
        # Check case of the leftmost character
        left = queue[0]

        if left.isupper():
            # lowercase entire queue
            queue = deque(ch.lower() for ch in queue)
        else:
            # uppercase entire queue
            queue = deque(ch.upper() for ch in queue)
    else:
        # Toggle only the leftmost character
        ch = queue.popleft()
        queue.appendleft(ch.swapcase())
    return backspace_count, "".join(queue)


"""
in normal words: delete previous or current word


inCamel: delete into you hit an uppercase if last letter was lower or upper if
it was lower, or if you hit a non_alphanumeric character

in_snake_case: delete until you hit _, SAME_HERE
unless we hit an uppercase/lowercase when the last letter was lower/upper


all-other-separators, will behave like snake case
"""


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
