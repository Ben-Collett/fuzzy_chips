import threading
from typing import TYPE_CHECKING
from buffer import KeyBuffer
from casing import Casing
from command_processor import CommandProcessor
from config_utils import create_config
from keyboard import KeyboardEvent
from config import Config

if TYPE_CHECKING:
    from main import AppContext


class AppContext:
    _current: "AppContext | None" = None

    def __init__(self):
        self.stop_event: threading.Event = threading.Event()
        self.current_casing: Casing = Casing.NORMAL
        self.expected_counter: int = 0
        self._buffer: KeyBuffer = KeyBuffer()
        self._right_arrow_buffer: KeyBuffer = KeyBuffer()
        self.just_set: threading.Event = threading.Event()
        self.prev_real_event: KeyboardEvent | None = None
        self.command_processor: CommandProcessor = None  # type: ignore
        self.ipc_enabled: list = []

        self.config: Config = None  # type: ignore

    @classmethod
    def get_current(cls) -> "AppContext":
        if cls._current is None:
            raise RuntimeError("AppContext not initialized")
        return cls._current

    def resize_buffers(self, size: int):
        self._buffer.update_capacity(size)
        self._right_arrow_buffer.update_capacity(size)

    @classmethod
    def initialize(cls) -> "AppContext":
        ctx = cls()
        cls._current = ctx
        ctx.config = create_config()
        ctx.resize_buffers(ctx.config.general.buffer_size)
        ctx.command_processor = cls._make_processor(ctx)
        cls._update_ipc_enabled(ctx)
        return ctx

    @staticmethod
    def _make_processor(ctx: "AppContext") -> CommandProcessor:
        from commands import make_processor

        command_processor = make_processor(ctx)
        return command_processor

    @staticmethod
    def _update_ipc_enabled(ctx: "AppContext"):
        ctx.command_processor.ipc_commands.clear()
        ctx.ipc_enabled = list(ctx.config.ipc.ipc_enabled_commands)
        for command in ctx.command_processor._commands.keys():
            if command in ctx.ipc_enabled:
                ctx.command_processor.ipc_commands.add(command)
