from collections import deque
from dataclasses import dataclass


@dataclass
class BufferEntry:
    char: str
    recent: bool


class KeyBuffer:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer: deque[BufferEntry] = deque(maxlen=capacity)

    def mark_recent_as_old(self):
        for i, entry in enumerate(self.buffer):
            self.buffer[i] = BufferEntry(entry.char, recent=False)

    def remove_first(self):
        if not self.is_empty():
            self.buffer.popleft()

    def is_equal(self, items):
        return self.get() == list(items)

    def clear(self):
        self.buffer.clear()

    def set_buffer(self, items, recent=True):
        self.clear()
        self.add_all(items, recent)

    def add_all(self, items, recent=True):
        for item in items:
            self.add(item, recent)

    def add_entry(self, entry: BufferEntry):
        """Add entry to the buffer (removes oldest if full)"""
        self.buffer.append(entry)

    def add(self, item, recent=True):
        """Add item to the buffer (removes oldest if full)"""
        self.add_entry(BufferEntry(item, recent))

    def get(self):
        """Get the current buffer as a list"""
        return [entry.char for entry in self.buffer]

    def __str__(self):
        return str(self.get())

    def get_word_count(self) -> int:
        """
        Return the total number of words in the buffer.
        A word is defined as a sequence of non-whitespace characters.
        """
        chars = self.get()
        if not chars:
            return 0

        count = 0
        in_word = False

        for c in chars:
            if c.isspace():
                in_word = False
            else:
                if not in_word:
                    count += 1
                    in_word = True

        return count

    def get_word_entries(self, index: int) -> list[BufferEntry]:
        """
        Get the word entries at the given index.
        Supports negative indexing (-1 = last word).
        Returns an empty list if index is out of range.
        """
        if not self.buffer:
            return []

        chars = self.get()
        words: list[tuple[int, int]] = []
        i = 0
        n = len(chars)

        while i < n:
            while i < n and chars[i].isspace():
                i += 1
            if i >= n:
                break

            start = i
            while i < n and not chars[i].isspace():
                i += 1
            end = i - 1

            words.append((start, end))

        if not words:
            return []

        if index < 0:
            index += len(words)

        if index < 0 or index >= len(words):
            return []

        start, end = words[index]
        return list(self.buffer)[start: end + 1]

    def get_word(self, index: int) -> str:
        """
        Get the word at the given index.
        Supports negative indexing (-1 = last word).
        Returns an empty string if index is out of range.
        """
        entries = self.get_word_entries(index)
        return "".join(e.char for e in entries)

    def get_word_and_new_state(self, index: int) -> tuple[str, list[bool]]:
        """
        Get the word at the given index and whether each character is new.
        Supports negative indexing (-1 = last word).
        Returns (word, is_new_list) tuple.
        """
        entries = self.get_word_entries(index)
        word = "".join(e.char for e in entries)
        is_new_list = [e.recent for e in entries]
        return word, is_new_list

    def get_leading_white_space(self) -> str:
        buffer: list[str] = self.get()
        end = 0
        for ch in buffer:
            if not ch.isspace():
                break
            end += 1
        if end == 0:
            return ""

        return "".join(buffer[0: end + 1])

    def get_white_space_before_prev_word(self) -> str:
        chars = self.get()
        if not chars:
            return ""

        i = len(chars) - 1

        # 1. Skip trailing whitespace
        while i >= 0 and chars[i].isspace():
            i -= 1

        # 2. Skip the previous word
        while i >= 0 and not chars[i].isspace():
            i -= 1

        # 3. Collect whitespace before the word
        end = i
        while i >= 0 and chars[i].isspace():
            i -= 1

        start = i + 1
        return "".join(chars[start: end + 1])

    def get_trailing_white_space(self) -> str:
        chars: list[str] = self.get()
        if len(chars) == 0:
            return ""
        upper = len(chars) - 1
        if not chars[upper].isspace():
            return ""
        lower = len(chars) - 1
        while lower > 0 and chars[lower].isspace():
            lower -= 1
        if lower > 0:
            lower += 1
        elif lower == 0 and not chars[lower].isspace():
            lower += 1

        return "".join(chars[lower: upper + 1])

    def should_captlize_prev_word(self, captilize_after=[], pass_through=[]) -> bool:
        chars: list[str] = self.get()
        target_range = KeyBuffer._get_prev_word_range(chars)
        if target_range is None:
            return False
        lower, _ = target_range
        if lower == 0:
            return False
        lower -= 1
        while lower > 0:
            if not chars[lower].isspace() and chars[lower] not in pass_through:
                break
            lower -= 1
        return chars[lower] in captilize_after

    def get_last_word(self) -> str:
        return self.get_word(-1)

    def get_prev_word_entries(self) -> list[BufferEntry]:
        return self.get_word_entries(-1)

    @staticmethod
    def _get_prev_word_range(chars: list[str]):
        if len(chars) == 0:
            return None
        upper = len(chars) - 1

        while chars[upper] == " " and upper > 0:
            upper -= 1
        if upper < 0 or chars[upper] == " ":
            return None
        lower = 0
        for i in range(upper, 0, -1):
            if chars[i] == " ":
                lower = i + 1
                break
        return (lower, upper)

    def backspace(self) -> str:
        if not self.is_empty():
            return self.buffer.pop().char

    def backspace_entry(self) -> BufferEntry:
        if not self.is_empty():
            return self.buffer.pop()

    def is_empty(self):
        return len(self.buffer) == 0

    def get_last(self):
        """Get the last inserted value"""
        if not self.is_empty():
            return self.buffer[-1].char
        else:
            return None  # Return None if buffer is empty

    def __len__(self):
        return len(self.buffer)
