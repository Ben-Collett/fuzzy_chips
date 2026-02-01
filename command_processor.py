from typing import Callable, List

CommandHandler = Callable[[List[str]], None]


class CommandProcessor:
    def __init__(self, fallback: Callable[[str], None] | None = None):
        self._commands: dict[str, CommandHandler] = {}
        self._ipc_commands: set[str] = set()
        self._fallback = fallback

    def has_command(self, cmd: str):
        return cmd in self._commands.keys()

    def register(self, name: str, handler: CommandHandler, ipc_enabled=False):
        self._commands[name] = handler
        if ipc_enabled:
            self._ipc_commands.add(name)

    def process(self, line: str):
        tokens = line.strip().split()
        if not tokens:
            return

        command = tokens[0]
        args = tokens[1:]

        handler = self._commands.get(command)
        if handler:
            handler(args)
        elif self._fallback:
            self._fallback(line)

    def process_ipc(self, line: str) -> str:
        tokens = line.strip().split()
        if not tokens:
            return "invalid"

        command = tokens[0]
        args = tokens[1:]

        if command not in self._commands:
            return "invalid"

        if command not in self._ipc_commands:
            return "not ipc enabled"

        try:
            handler = self._commands[command]
            handler(args)
            return "succeeded"
        except Exception:
            return "invalid"
