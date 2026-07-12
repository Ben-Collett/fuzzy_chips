from typing import override
from mouse import Mouse
from config_wrapper import ConfigWrapper
from config import Config
from my_keyboard import Keyboard
from main_context import AppContext
from keyboard._mouse_event import ButtonEvent, LEFT, DOWN, UP
from testing_utils import make_down_up_events


class KeyboardMock(Keyboard):
    def __init__(self):
        self.callbacks = []
        self.events_to_run = []
        self.priority_events = []
        self.written_event_names: list[str] = []

    def flush_events_to_run(self):
        while self.events_to_run or self.priority_events:
            while self.priority_events:
                event = self.priority_events.pop(0)
                for callback in self.callbacks:
                    callback(event)
            if self.events_to_run:
                event = self.events_to_run.pop(0)
                for callback in self.callbacks:
                    callback(event)

    @override
    def write(self, characters: str):
        for ch in characters:
            self.written_event_names.append(ch)
            down, up = make_down_up_events(ch)
            self.priority_events.extend([down, up])

    def write_list(self, s: list[str]):
        for ev in s:
            if ev == "backspace":
                self.backspace()
            elif ev == "left":
                self.left()
            elif ev == "delete":
                self.delete()
            else:
                self.write(ev)

    @override
    def backspace(self, n_times: int = 1):
        for _ in range(n_times):
            self.written_event_names.append("backspace")
            down, up = make_down_up_events("backspace")
            self.priority_events.extend([down, up])

    def left(self):
        self.written_event_names.append("left")
        down, up = make_down_up_events("left")
        self.priority_events.extend([down, up])

    def delete(self):
        self.written_event_names.append("delete")
        down, up = make_down_up_events("delete")
        self.priority_events.extend([down, up])

    @override
    def hook(self, callback):
        self.callbacks.append(callback)


class MouseMock(Mouse):
    def __init__(self):
        self.callbacks = []

    @override
    def hook(self, callback):
        self.callbacks.append(callback)

    def _send_event(self, event):
        for callback in self.callbacks:
            callback(event)

    def left_click(self):
        self._send_event(ButtonEvent(event_type=DOWN, button=LEFT, time=1))
        self._send_event(ButtonEvent(event_type=UP, button=LEFT, time=2))


class ConfigWrapperMock(ConfigWrapper):
    def __init__(self, config: Config | None = None):
        if config is None:
            config = Config()
        super().__init__(config)
        self.reload_count = 0
        self.on_reload: dict | None = None

    def set_on_reload(self, on_reload: dict | None):
        self.on_reload = on_reload

    @override
    def reload_config(self, override: dict | None = None):
        self.reload_count += 1
        if override is not None:
            self._config.update(override)
        else:
            self._config.update(self.on_reload)


class AppContextMock(AppContext):
    @classmethod
    def initialize(cls, *args, **kwargs):
        raise AssertionError(
            "Called AppContextMock.initialize() instead of AppContext.initialize()"
        )

    def __init__(self, config_wrapper: ConfigWrapperMock | None = None):
        super().__init__()
        if config_wrapper:
            self.config_wrapper = config_wrapper
        else:
            self.config_wrapper = ConfigWrapperMock()
        self.keyboard = KeyboardMock()
        self.mouse = MouseMock()

    def left_click(self):
        assert isinstance(self.mouse, MouseMock), "mouse isn't a mock somehow"
        self.mouse.left_click()

    def reload_count(self) -> int:
        assert isinstance(
            self.config_wrapper, ConfigWrapperMock), "config wrapper is not a mock somehow"
        return self.config_wrapper.reload_count

    def set_on_reload(self, config: dict):
        assert isinstance(
            self.config_wrapper, ConfigWrapperMock), "config wrapper is not a mock somehow"
        self.config_wrapper.set_on_reload(config)

    def written_event_names(self):
        assert isinstance(
            self.keyboard, KeyboardMock), "keyboard not mock somehow"
        return self.keyboard.written_event_names

    def buffers_to_str(self):
        return "".join(self._buffer.get())+"".join(reversed(self.right_arrow_buffer.get()))

    def count_writes(self, event_name: str) -> int:
        assert isinstance(
            self.keyboard, KeyboardMock), "keyboard not mock somehow"
        count = 0
        for name in self.keyboard.written_event_names:
            if name == event_name:
                count += 1
        return count
