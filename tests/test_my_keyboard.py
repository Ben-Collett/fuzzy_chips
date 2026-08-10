import my_keyboard
from my_keyboard import Keyboard


class TestKeyboardBackspace:
    def _make_keyboard(self, monkeypatch, grabbed: bool):
        keyboard = Keyboard.__new__(Keyboard)
        recorded = []

        def fake_release(key):
            recorded.append(("release", key))

        def fake_press_and_release(key):
            recorded.append(("press_and_release", key))

        monkeypatch.setattr(
            my_keyboard.keyboard, "is_grabbed", lambda: grabbed)
        monkeypatch.setattr(my_keyboard.keyboard, "release", fake_release)
        monkeypatch.setattr(
            my_keyboard.keyboard, "press_and_release", fake_press_and_release)
        return keyboard, recorded

    def test_grabbed_releases_before_writing(self, monkeypatch):
        keyboard, recorded = self._make_keyboard(monkeypatch, grabbed=True)

        keyboard.backspace(3)

        assert recorded == [
            ("release", "backspace"),
            ("press_and_release", "backspace"),
            ("press_and_release", "backspace"),
            ("press_and_release", "backspace"),
        ]

    def test_not_grabbed_does_not_release(self, monkeypatch):
        keyboard, recorded = self._make_keyboard(monkeypatch, grabbed=False)

        keyboard.backspace(2)

        assert recorded == [
            ("press_and_release", "backspace"),
            ("press_and_release", "backspace"),
        ]

    def test_zero_times_writes_nothing(self, monkeypatch):
        keyboard, recorded = self._make_keyboard(monkeypatch, grabbed=True)

        keyboard.backspace(0)

        assert recorded == []
